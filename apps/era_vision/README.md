# ERA Vision

Custom Frappe app for managing computer vision models, tracked objects, regions of interest, algorithms, jobs, and results.

## App layout

- `era_vision/vision/doctype/`: Vision configuration and result DocTypes.
- `era_vision/vision/page/`: Desk pages for dashboards and result review.
- `era_vision/api.py`: app API entry points.
- `era_vision/services/`: model and inference service integrations.
- `era_vision/tasks.py`: background job entry points.
- `era_vision/public/`: app frontend assets.

Inference is intentionally left as an integration point; this scaffold does not include a model runtime.
