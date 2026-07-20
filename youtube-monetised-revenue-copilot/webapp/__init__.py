"""Web dashboard for ytcopilot — a thin FastAPI layer over the same
modules the CLI uses (youtube_data, monetization, research, generate_text,
generate_thumbnail, content_authenticity). No logic is duplicated here;
this package only handles HTTP routing, forms, and rendering."""
