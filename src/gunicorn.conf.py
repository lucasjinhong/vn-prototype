# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 3

accesslog = "-"
errorlog = "-"
loglevel = "info"

access_log_format = '%(h)s %(t)s "%(r)s" %(s)s %(b)s [took %(D)sµs]'

def pre_request(worker, req):
    if req.path in ["/healthz", "/status"]:
        req.log_already = True