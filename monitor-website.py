import time
import requests
import smtplib
import os
import paramiko
import linode_api4
import schedule


EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
REMOTE_SERVER = os.environ.get('REMOTE_SERVER')
PUBLIC_IP = os.environ.get('PUBLIC_IP')
SSH_KEY_FILEPATH = os.environ.get('SSH_KEY_FILEPATH')
LINODE_TOKEN = os.environ.get('LINODE_TOKEN')

def send_notification(email_msg):
    print("Sending an email...")
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        message = f"Subject: SITE DOWN\n {email_msg}"
        smtp.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, message)

def restart_container():
    print("Restarting the application...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PUBLIC_IP, username='root', key_filename=SSH_KEY_FILEPATH)
    stdin, stdout, stderr = ssh.exec_command('docker start 1634e28508ea')
    print(stdout.readlines())
    ssh.close()

def restart_container_and_app():
    linode = linode_api4.LinodeClient(LINODE_TOKEN)
    nginx_server = linode.load(linode_api4.Instance, 65539523)
    nginx_server.reboot()

    while True:
        nginx_server = linode.load(linode_api4.Instance, 65539523)
        if nginx_server.status == 'running':
            time.sleep(5)
            restart_container()
            break

def monitor_application():
    try:
        response = requests.get(REMOTE_SERVER)
        if False:
            print('Application is running successfully!')
        else:
            print('Application is down!')
            email_body = f"Application returned {response.status_code} Application needs to be restarted"
            send_notification(email_body)
            restart_container()
    except Exception as ex:
        print(f'Connection error has occurred: {ex}')
        email_body = "Application is not accessible"
        send_notification(email_body)
        restart_container_and_app()

schedule.every(5).minutes.do(monitor_application)

while True:
    schedule.run_pending()