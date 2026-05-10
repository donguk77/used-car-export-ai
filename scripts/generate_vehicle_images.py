"""scripts/generate_vehicle_images.py — Gemini Imagen 으로 차량 사진 자동 생성.

사용법:
    py -X utf8 scripts/generate_vehicle_images.py            # image_url=NULL 만
    py -X utf8 scripts/generate_vehicle_images.py --all      # 강제 재생성
    py -X utf8 scripts/generate_vehicle_images.py --vehicle-id <UUID>

저장 위치:
    frontend/public/vehicle-images/{vehicle_id}.png
    (Vite 가 /vehicle-images/{id}.png 로 자동 서빙)

비용: ~$0.04 / 이미지 (Imagen 3). 10대 ≈ $0.40.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Vehicle  # noqa: E402

OUTPUT_DIR = ROOT / "frontend" / "public" / "vehicle-images"
PUBLIC_PREFIX = "/vehicle-images"

# 시도 모델 — 첫 번째가 실패하면 다음 시도
IMAGEN_MODELS = [
    "imagen-3.0-generate-002",
    "imagen-3.0-generate-001",
    "imagen-4.0-generate-001",
]


def build_prompt(v: Vehicle) -> str:
    """차량 사양 → 사실적인 자동차 사진 프롬프트."""
    color = (v.color_exterior or "metallic silver").strip()
    year = v.year or 2020
    make = v.make or "Hyundai"
    model = v.model or "sedan"

    body_descriptor = {
        "passenger": "modern 4-door sedan" if model.lower() in {"sonata", "avante", "k5", "k3", "g80"} else "modern SUV",
        "truck": "compact pickup truck",
        "van": "passenger minivan",
    }.get(v.body_type or "passenger", "modern car")

    return (
        f"Professional automotive product photography of a {year} {make} {model}, "
        f"a {body_descriptor}, painted {color}, clean studio shot, "
        f"three-quarter front-side angle view, soft natural lighting, "
        f"neutral light gray seamless background, no text, no logos, no people, "
        f"high resolution photorealistic style, automotive marketing catalog quality"
    )


def generate_image_imagen(prompt: str, api_key: str) -> bytes:
    """Imagen 호출. 시도 모델 순회하며 첫 성공 사용."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    last_err: Exception | None = None
    for model_name in IMAGEN_MODELS:
        try:
            response = client.models.generate_images(
                model=model_name,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                ),
            )
            if response.generated_images:
                img = response.generated_images[0].image
                # SDK 버전에 따라 image_bytes 또는 _image_bytes
                bytes_data = getattr(img, "image_bytes", None) or getattr(img, "_image_bytes", None)
                if bytes_data:
                    print(f"      [model={model_name}]")
                    return bytes_data
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue
    raise RuntimeError(f"All Imagen models failed. Last error: {last_err}")


def generate_image_gemini_fallback(prompt: str, api_key: str) -> bytes:
    """Gemini 2.5 Flash Image (preview) 폴백."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    for model_name in ["gemini-2.5-flash-image-preview", "gemini-2.0-flash-exp-image-generation"]:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
            )
            for part in response.candidates[0].content.parts:
                inline = getattr(part, "inline_data", None)
                if inline and inline.data:
                    print(f"      [fallback model={model_name}]")
                    return inline.data
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError("Both Imagen + Gemini image generation failed")


def generate_image(prompt: str, api_key: str) -> bytes:
    try:
        return generate_image_imagen(prompt, api_key)
    except RuntimeError as imagen_err:
        print(f"      ! Imagen failed: {imagen_err}, trying Gemini fallback...")
        return generate_image_gemini_fallback(prompt, api_key)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="기존 image_url 도 재생성 (덮어쓰기)")
    parser.add_argument("--vehicle-id", help="특정 차량 ID 만")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.gemini_api_key:
        print("ERROR: .env 의 GEMINI_API_KEY 가 비어있습니다.", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  output dir: {OUTPUT_DIR.relative_to(ROOT)}")

    with SessionLocal() as session:
        stmt = select(Vehicle)
        if args.vehicle_id:
            stmt = stmt.where(Vehicle.id == args.vehicle_id)
        elif not args.all:
            stmt = stmt.where(Vehicle.image_url.is_(None))
        stmt = stmt.order_by(Vehicle.created_at)
        vehicles = list(session.execute(stmt).scalars())

        if not vehicles:
            print("  no vehicles to process. (try --all to regenerate)")
            return

        print(f"  {len(vehicles)} vehicle(s) to process. estimated cost ≈ ${len(vehicles) * 0.04:.2f}\n")

        ok_count = 0
        for v in vehicles:
            label = f"{v.make or '?'} {v.model or '?'} {v.year or ''}".strip()
            print(f"  → {label}  (id={str(v.id)[:8]})")
            prompt = build_prompt(v)
            print(f"    prompt: {prompt[:100]}...")
            try:
                image_bytes = generate_image(prompt, settings.gemini_api_key)
                filename = f"{v.id}.png"
                output_path = OUTPUT_DIR / filename
                output_path.write_bytes(image_bytes)
                v.image_url = f"{PUBLIC_PREFIX}/{filename}"
                print(f"    ✓ saved {filename}  ({len(image_bytes):,} bytes)\n")
                ok_count += 1
            except Exception as e:  # noqa: BLE001
                print(f"    ✗ {type(e).__name__}: {e}\n", file=sys.stderr)
                continue
        session.commit()

        print(f"  done. {ok_count}/{len(vehicles)} succeeded.")
        if ok_count < len(vehicles):
            sys.exit(1)


if __name__ == "__main__":
    main()
