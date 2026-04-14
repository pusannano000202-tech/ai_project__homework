from __future__ import annotations

import base64
import io
import math
from collections import deque

import numpy as np
from PIL import Image, ImageDraw


class ContactAngleError(ValueError):
    pass


def analyze_contact_angle(image_bytes: bytes) -> dict[str, object]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = _resize_for_analysis(image)
    gray = np.asarray(image.convert("L"), dtype=np.uint8)

    if gray.shape[0] < 80 or gray.shape[1] < 80:
        raise ContactAngleError("이미지가 너무 작습니다. 측면 사진을 조금 더 크게 올려 주세요.")

    threshold = _otsu_threshold(gray)
    low_mask = gray <= threshold
    high_mask = gray >= threshold
    droplet_mask = _pick_droplet_mask(low_mask, high_mask, gray.shape)
    droplet_mask = _largest_component(droplet_mask)

    area_ratio = float(droplet_mask.mean())
    if area_ratio < 0.01:
        raise ContactAngleError("물방울 윤곽을 충분히 찾지 못했습니다. 배경 대비가 더 큰 사진을 사용해 주세요.")
    if area_ratio > 0.55:
        raise ContactAngleError("물방울 영역이 너무 넓게 잡혔습니다. 배경이 단순한 측면 사진을 사용해 주세요.")

    boundary_points = _extract_boundary_points(droplet_mask)
    if len(boundary_points) < 40:
        raise ContactAngleError("윤곽선 포인트가 부족해 접촉각을 계산할 수 없습니다.")

    baseline_y = _estimate_baseline(droplet_mask, boundary_points)
    fit_margin = max(5, int(gray.shape[0] * 0.02))
    fit_points = boundary_points[boundary_points[:, 1] < baseline_y - fit_margin]
    if len(fit_points) < 30:
        fit_points = boundary_points

    center_x, center_y, radius = _fit_circle(fit_points)
    if radius <= 1:
        raise ContactAngleError("물방울 곡면을 원호로 근사할 수 없습니다.")

    distance_from_center = baseline_y - center_y
    cosine_value = _clamp(-distance_from_center / radius, -1.0, 1.0)
    contact_angle_deg = math.degrees(math.acos(cosine_value))

    if not 5 <= contact_angle_deg <= 175:
        raise ContactAngleError("계산된 접촉각이 비정상 범위입니다. 다른 사진으로 다시 시도해 주세요.")

    left_contact_x, right_contact_x = _estimate_contact_points(
        droplet_mask,
        boundary_points,
        baseline_y,
        center_x,
        center_y,
        radius,
    )

    annotated = _draw_annotation(
        image=image,
        boundary_points=boundary_points,
        baseline_y=baseline_y,
        center_x=center_x,
        center_y=center_y,
        radius=radius,
        left_contact_x=left_contact_x,
        right_contact_x=right_contact_x,
    )

    result_label = "소수성 경향" if contact_angle_deg >= 90 else "친수성 경향"
    return {
        "contact_angle_deg": round(contact_angle_deg, 1),
        "baseline_y_px": round(float(baseline_y), 1),
        "radius_px": round(float(radius), 1),
        "classification": result_label,
        "analysis_note": (
            "가장 큰 물방울 실루엣을 찾은 뒤 원호(cap)로 근사한 추정값입니다. "
            "측면 사진, 단순한 배경, 수평한 시료면일수록 더 안정적으로 동작합니다."
        ),
        "preview_image": _image_to_data_url(image),
        "annotated_image": _image_to_data_url(annotated),
    }


def _resize_for_analysis(image: Image.Image) -> Image.Image:
    resized = image.copy()
    resized.thumbnail((1200, 900))
    return resized


def _otsu_threshold(gray: np.ndarray) -> int:
    histogram = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    total = histogram.sum()
    if total == 0:
        return 127

    cumulative_weight = np.cumsum(histogram)
    cumulative_mean = np.cumsum(histogram * np.arange(256))
    global_mean = cumulative_mean[-1]

    numerator = (global_mean * cumulative_weight - cumulative_mean) ** 2
    denominator = cumulative_weight * (total - cumulative_weight)
    valid = denominator > 0
    variance = np.zeros_like(numerator)
    variance[valid] = numerator[valid] / denominator[valid]
    return int(np.argmax(variance))


def _pick_droplet_mask(low_mask: np.ndarray, high_mask: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    corner_low = _corner_ratio(low_mask, shape)
    corner_high = _corner_ratio(high_mask, shape)
    return low_mask if corner_low < corner_high else high_mask


def _corner_ratio(mask: np.ndarray, shape: tuple[int, int]) -> float:
    height, width = shape
    patch = max(8, min(height, width) // 12)
    corners = np.concatenate(
        [
            mask[:patch, :patch].ravel(),
            mask[:patch, -patch:].ravel(),
            mask[-patch:, :patch].ravel(),
            mask[-patch:, -patch:].ravel(),
        ]
    )
    return float(corners.mean())


def _largest_component(mask: np.ndarray) -> np.ndarray:
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    best_pixels: list[tuple[int, int]] = []
    fallback_pixels: list[tuple[int, int]] = []

    for start_y, start_x in np.argwhere(mask):
        sy = int(start_y)
        sx = int(start_x)
        if visited[sy, sx]:
            continue

        queue: deque[tuple[int, int]] = deque([(sy, sx)])
        visited[sy, sx] = True
        pixels: list[tuple[int, int]] = []
        touches_top = False
        touches_left = False
        touches_right = False

        while queue:
            y, x = queue.popleft()
            pixels.append((y, x))

            if y == 0:
                touches_top = True
            if x == 0:
                touches_left = True
            if x == width - 1:
                touches_right = True

            for next_y, next_x in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= next_y < height and 0 <= next_x < width:
                    if mask[next_y, next_x] and not visited[next_y, next_x]:
                        visited[next_y, next_x] = True
                        queue.append((next_y, next_x))

        if len(pixels) > len(fallback_pixels):
            fallback_pixels = pixels

        if not touches_top and not touches_left and not touches_right and len(pixels) > len(best_pixels):
            best_pixels = pixels

    selected = best_pixels or fallback_pixels
    if not selected:
        raise ContactAngleError("물방울 실루엣을 찾지 못했습니다.")

    component = np.zeros_like(mask, dtype=bool)
    for y, x in selected:
        component[y, x] = True
    return component


def _extract_boundary_points(component: np.ndarray) -> np.ndarray:
    interior = component.copy()
    interior[1:-1, 1:-1] = (
        component[1:-1, 1:-1]
        & component[:-2, 1:-1]
        & component[2:, 1:-1]
        & component[1:-1, :-2]
        & component[1:-1, 2:]
    )
    boundary = component & ~interior
    ys, xs = np.nonzero(boundary)
    return np.column_stack([xs.astype(float), ys.astype(float)])


def _estimate_baseline(component: np.ndarray, boundary_points: np.ndarray) -> float:
    row_counts = component.sum(axis=1)
    height = component.shape[0]
    lower_start = int(height * 0.45)
    lower_counts = row_counts.copy()
    lower_counts[:lower_start] = 0

    peak = int(lower_counts.max())
    if peak <= 0:
        return float(boundary_points[:, 1].max())

    strong_rows = np.where(lower_counts >= peak * 0.86)[0]
    if len(strong_rows) == 0:
        return float(boundary_points[:, 1].max())
    return float(strong_rows.mean())


def _fit_circle(points: np.ndarray) -> tuple[float, float, float]:
    x = points[:, 0]
    y = points[:, 1]
    matrix = np.column_stack([x, y, np.ones_like(x)])
    target = -(x**2 + y**2)
    coeffs, _, _, _ = np.linalg.lstsq(matrix, target, rcond=None)
    a, b, c = coeffs
    center_x = -a / 2
    center_y = -b / 2
    radius_sq = center_x**2 + center_y**2 - c
    if radius_sq <= 0:
        raise ContactAngleError("원호 적합에 실패했습니다.")
    return float(center_x), float(center_y), float(math.sqrt(radius_sq))


def _estimate_contact_points(
    component: np.ndarray,
    boundary_points: np.ndarray,
    baseline_y: float,
    center_x: float,
    center_y: float,
    radius: float,
) -> tuple[float, float]:
    tolerance = 3.0
    near_baseline = boundary_points[
        (boundary_points[:, 1] >= baseline_y - tolerance)
        & (boundary_points[:, 1] <= baseline_y + tolerance)
    ]
    if len(near_baseline) >= 2:
        return float(near_baseline[:, 0].min()), float(near_baseline[:, 0].max())

    baseline_row = min(max(int(round(baseline_y)), 0), component.shape[0] - 1)
    xs = np.where(component[baseline_row])[0]
    if len(xs) >= 2:
        return float(xs.min()), float(xs.max())

    dx = math.sqrt(max(radius**2 - (baseline_y - center_y) ** 2, 0.0))
    return center_x - dx, center_x + dx


def _draw_annotation(
    image: Image.Image,
    boundary_points: np.ndarray,
    baseline_y: float,
    center_x: float,
    center_y: float,
    radius: float,
    left_contact_x: float,
    right_contact_x: float,
) -> Image.Image:
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    width, _ = annotated.size

    for point_x, point_y in boundary_points[:: max(1, len(boundary_points) // 800)]:
        draw.ellipse(
            (point_x - 1, point_y - 1, point_x + 1, point_y + 1),
            fill=(255, 99, 132),
        )

    draw.line((0, baseline_y, width, baseline_y), fill=(255, 209, 102), width=3)
    draw.ellipse(
        (center_x - radius, center_y - radius, center_x + radius, center_y + radius),
        outline=(80, 200, 255),
        width=3,
    )

    for contact_x in (left_contact_x, right_contact_x):
        draw.ellipse(
            (contact_x - 6, baseline_y - 6, contact_x + 6, baseline_y + 6),
            fill=(126, 234, 136),
        )

    draw.ellipse(
        (center_x - 5, center_y - 5, center_x + 5, center_y + 5),
        fill=(255, 255, 255),
    )
    return annotated


def _image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
