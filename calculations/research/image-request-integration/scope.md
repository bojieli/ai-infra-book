# C66 serial image request public boundary

Original chapter12.1/experiment12-1 permits actual file bytes or supplied metadata. This calculation takes explicit input/transmitted/final bytes, upload/download rates, and individually declared preparation, connection, RTT residual, queue, file decode, model, final encode and usable-output times. It does not derive RAW/JPEG size from pixels or VAE tensor size.

The original 30MB/5MB,20/100Mbit/s,100ms residual RTT and0.3s model total12.8s is reproduced exactly. Model0.03s saves0.27s. Same-quality compressed15MB plus0.3s extra codec work saves5.7s at20Mbit/s, ties at400Mbit/s, loses above. The remote/local5s threshold is400/7 Mbit/s uncompressed and400/13 compressed. Unknown local time and no finite winning upload rate are distinct outcomes; reuse removes only connection cost.

The quality requirement is an explicit comparison assumption, not measured codec quality. Default zero costs are declared teaching inputs. The RTT budget is charged once; placing it before upload in the additive record does not assert actual propagation chronology. The figure therefore uses additive budget composition and a separate data-dependency path, not a packet timeline.

Figure12-1 covers the original data path and complete-image versus upload curves,791 exact samples, and marks preview unknown. It must not be used as evidence for first-preview or streaming delivery. Original chapter12.1.2 also asks for dependency-permitted chunk overlap and separate preview/final delivery; research/image-request-streaming is a separate candidate for that requirement. Until it is independently accepted and publicly integrated, C66 remains open.

Validation of this delivery includes the reviewed serial candidate, public boundary tests, actual JSON/Markdown CLI equality, frozen outputs, candidate/public figure equality, registered hashes and outline checks. Overall book coverage is not inferred from these gates.
