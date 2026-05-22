# Cryptography Policy

## 1. Algorithms
AES-256 for data at rest. TLS 1.2+ for in-transit.

## 2. Key Management
AWS KMS is authoritative. Keys are automatically rotated every 365 days.