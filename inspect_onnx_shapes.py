import onnx

for path in ["/mnt/d/A1/ppocrv4_det.onnx", "/mnt/d/A1/ppocrv4_rec.onnx"]:
    model = onnx.load(path)
    print("MODEL", path)
    for value in model.graph.input:
        dims = []
        for dim in value.type.tensor_type.shape.dim:
            dims.append(dim.dim_value if dim.dim_value else dim.dim_param or "?")
        print(" input", value.name, dims)
    for value in model.graph.output:
        dims = []
        for dim in value.type.tensor_type.shape.dim:
            dims.append(dim.dim_value if dim.dim_value else dim.dim_param or "?")
        print(" output", value.name, dims)
