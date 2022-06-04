from time import sleep
from distutils.util import strtobool
from app.utils import get_api
from app.utils import send_email

def get_mail_addresses_for_pools(pools):
    prefixes = []
    for pool in pools.split(','):
        prefixes.extend(get_api().get_prefixes_by_pool_name(pool))

    return set([p.customer_id for p in prefixes if p.customer_id and '@' in p.customer_id])


def send_mail_to_pools(pools, subject, template, delay):
    print("Loading data...\n")

    recipients = get_mail_addresses_for_pools(pools)

    print("Template\n========\n")
    print(template)

    print(("\nSending this as an email to %d recipients of pool(s) %s: y/N" % \
            (len(recipients), pools)))
    raw = input().lower()
    if raw and strtobool(raw):
        size = len(recipients)
        for i,email in enumerate(recipients):
            send_email(email, subject, template, {}, no_template = True)
            print(("%f [%d/%d] %s" % (i/size, i, size, email)))
            sleep(float(delay))
    else:
        print("Aborted")
