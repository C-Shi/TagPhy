# Local ONNX models

Place weights here. They are not committed (see `.gitignore`).

## NSFW pre-check (`nsfw.onnx`)

Expected path: `/models/nsfw_mobilenet2_224x224.onnx` (GantMan MobileNetV2 NSFW classifier, 224×224, 5-class).

This is the neural net behind NSFWJS, run as ONNX via `onnxruntime` — not the JavaScript library.

If the file is missing, `NSFWPreCheck` fails closed (no Gemini, file left in place). There is no auto-download.

Obtain a conversion of GantMan `nsfw_mobilenet2.224x224.h5`, for example:
