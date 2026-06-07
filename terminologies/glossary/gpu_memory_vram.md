# GPU memory / VRAM

The GPU's main on-board memory (the advertised "40 GB" / "80 GB"), holding the model weights *and* every active request's KV cache. Fast versus CPU RAM but comparatively **slow** versus on-chip SRAM (~1.5–3 TB/s), and limited — when it fills up you must drop requests or shrink the batch, so VRAM is the scarce resource. Hardware folks call it **HBM (High-Bandwidth Memory)**.
