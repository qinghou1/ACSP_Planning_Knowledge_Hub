# Shared resource data

The original HTML contained no resource records. This directory intentionally starts empty apart from documentation.

Add one validated resource object per JSON file. Its filename must equal its ID. Use a collection subfolder or `general/`; link multiple collections through `collectionIds` in the single record. Do not copy fictional examples here. Do not commit raw exported workspace packets here; import them using `scripts/import_packet.py` or copy only a validated packet's `record` object.

Published records need a real source URL and complete public metadata. A merge and successful deployment, not a local draft save, updates the public catalog.
