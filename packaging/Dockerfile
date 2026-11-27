FROM bolt-loop-course:20261124-group4-experiment
COPY . /opt/tail-course/
RUN chmod +x /opt/tail-course/frozen/llvm-bolt /opt/tail-course/frozen/o3 /opt/tail-course/frozen/pgo /opt/tail-course/frozen/old /opt/tail-course/frozen/tail /opt/tail-course/tests/*/original /opt/tail-course/tests/*/tail
ENTRYPOINT ["python3", "/opt/tail-course/scripts/run.py"]
