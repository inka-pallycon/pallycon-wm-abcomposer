# ABComposer Sample for PallyCon DRM CLI Packager

This app is a sample program that composes DASH / HLS / CMAF streams to enable Pallycon Forensic Watermark.

## Requirements

This app is implemented to support the following cases:
- Input media
  - preprocessed by the PallyCon Forensic Watermark [Preprocessor SDK](https://pallycon.com/docs/en/forensic-watermarking/preprocessing/preprocessor-library/) or [FFmpeg Preprocessor Filter](https://pallycon.com/docs/en/forensic-watermarking/preprocessing/ffmpeg-filter/)
  - packaged by the PallyCon DRM CLI Packager
- CDN Embedder
  - [Akamai Adaptive Media Delivery Watermarking](https://techdocs.akamai.com/adaptive-media-delivery/docs/add-wmk)
    - Notice: It does not support CMAF.
  - AWS CloudFront CDN and [AWS CloudFront Embedder by PallyCon](https://pallycon.com/docs/en/forensic-watermarking/embedding/cloudfront-embedder/)

The other cases are not considered.

## Environments

Python 3.6

## Usage

Simply run it as follows:
```
python3 ABComposer.py <stream dir 0> <stream dir 1> <target dir> [--remove_src] [--overwrite]
```

As a default, it copies the sources to the target and keeps the sources. If you want to remove the sources after composing, you can use `--remove_src` option. It moves the sources instead copying and removes remainings.

And if the `<target dir>` already exists, it exits without composing. If you use `--overwrite`, it overwrites the `<target dir>`.

***

https://pallycon.com | obiz@inka.co.kr (Global), cbiz@inka.co.kr (Korea)

Copyright 2024 INKA Entworks. All Rights Reserved.
