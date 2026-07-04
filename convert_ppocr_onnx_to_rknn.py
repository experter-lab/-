import argparse
from pathlib import Path

from rknn.api import RKNN


def convert_onnx_to_rknn(
    model_name,
    onnx_path,
    rknn_path,
    target_platform="rk3588",
    mean_values=None,
    std_values=None,
):
    onnx_path = Path(onnx_path)
    rknn_path = Path(rknn_path)
    rknn_path.parent.mkdir(parents=True, exist_ok=True)

    rknn = RKNN(verbose=True)
    print(f"[{model_name}] config")
    mean_values = mean_values or [[0, 0, 0]]
    std_values = std_values or [[1, 1, 1]]
    ret = rknn.config(
        target_platform=target_platform,
        mean_values=mean_values,
        std_values=std_values,
        quant_img_RGB2BGR=False,
    )
    if ret != 0:
        raise RuntimeError(f"{model_name}: config failed: {ret}")

    print(f"[{model_name}] load_onnx {onnx_path}")
    ret = rknn.load_onnx(model=str(onnx_path))
    if ret != 0:
        raise RuntimeError(f"{model_name}: load_onnx failed: {ret}")

    print(f"[{model_name}] build")
    ret = rknn.build(do_quantization=False)
    if ret != 0:
        raise RuntimeError(f"{model_name}: build failed: {ret}")

    print(f"[{model_name}] export {rknn_path}")
    ret = rknn.export_rknn(str(rknn_path))
    if ret != 0:
        raise RuntimeError(f"{model_name}: export_rknn failed: {ret}")
    rknn.release()
    print(f"[{model_name}] ok: {rknn_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", default="/mnt/d/A1/rknn_ppocr")
    parser.add_argument("--det-onnx", default="/mnt/d/A1/ppocrv4_det.onnx")
    parser.add_argument("--rec-onnx", default="/mnt/d/A1/ppocrv4_rec.onnx")
    parser.add_argument("--target-platform", default="rk3588")
    args = parser.parse_args()

    workdir = Path(args.workdir)
    convert_onnx_to_rknn(
        "ppocr_det",
        args.det_onnx,
        workdir / "ppocrv4_det_rk3588.rknn",
        args.target_platform,
        mean_values=[[123.675, 116.28, 103.53]],
        std_values=[[58.395, 57.12, 57.375]],
    )
    convert_onnx_to_rknn(
        "ppocr_rec",
        args.rec_onnx,
        workdir / "ppocrv4_rec_rk3588.rknn",
        args.target_platform,
        mean_values=[[0, 0, 0]],
        std_values=[[1, 1, 1]],
    )


if __name__ == "__main__":
    main()
