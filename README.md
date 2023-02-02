# s3etag
Compute md5-based ETag of a local file and compare to remote ETag in S3.

Usage:
```
s3etag.py --local-file path/to/file.tar.gz --bucket my-bucket --key long/object/key/name/file.tar.gz --s3-access-key ACCESSKEY --s3-secret-key SECRETKEY --s3-endpoint https://s3.ki.se
```

The code is based on examples from the following StackOverflow thread:
https://stackoverflow.com/questions/12186993/what-is-the-algorithm-to-compute-the-amazon-s3-etag-for-a-file-larger-than-5gb

