try:
    from rknnlite.api import RKNNLite
except Exception:
    RKNNLite = None

try:
    from rknn.api import RKNN
except Exception:
    RKNN = None

try:
    import numpy as np
except Exception:
    np = None


class RKNN_model_container:
    def __init__(self, model_path, target=None, device_id=None) -> None:
        if RKNNLite is not None:
            rknn = RKNNLite()
            ret = rknn.load_rknn(model_path)
            if ret != 0:
                raise RuntimeError(f"load_rknn failed: {ret}")
            print("--> Init RKNNLite runtime environment")
            core_mask = getattr(RKNNLite, "NPU_CORE_AUTO", 0)
            ret = rknn.init_runtime(core_mask=core_mask)
        elif RKNN is not None:
            rknn = RKNN()
            ret = rknn.load_rknn(model_path)
            if ret != 0:
                raise RuntimeError(f"load_rknn failed: {ret}")
            print("--> Init RKNN runtime environment")
            if target is None:
                ret = rknn.init_runtime()
            else:
                ret = rknn.init_runtime(target=target, device_id=device_id)
        else:
            raise RuntimeError("Neither rknnlite.api nor rknn.api is available")

        if ret != 0:
            raise RuntimeError(f"init_runtime failed: {ret}")
        print("done")
        self.rknn = rknn

    def run(self, inputs):
        if self.rknn is None:
            print("ERROR: rknn has been released")
            return []
        if not isinstance(inputs, (list, tuple)):
            inputs = [inputs]
        if RKNNLite is not None and isinstance(self.rknn, RKNNLite):
            normalized = []
            for item in inputs:
                if np is not None and isinstance(item, np.ndarray) and item.ndim == 3:
                    item = item.reshape(1, *item.shape)
                normalized.append(item)
            inputs = normalized
        return self.rknn.inference(inputs=inputs)

    def release(self):
        self.rknn.release()
        self.rknn = None
