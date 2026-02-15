import boto3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import os

# AWS credentials from environment
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
REGION = os.environ.get("AWS_DEFAULT_REGION")
BUCKET = os.environ.get("S3_BUCKET")

# Create AWS clients
ec2 = boto3.client(
    "ec2",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

ce = boto3.client(
    "ce",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name="us-east-1"
)

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

# Fetch EC2 instances
instances = ec2.describe_instances()

instance_ids = []
for reservation in instances["Reservations"]:
    for instance in reservation["Instances"]:
        instance_ids.append(instance["InstanceId"])

# Fetch billing info
today = datetime.utcnow().strftime("%Y-%m-%d")

cost = ce.get_cost_and_usage(
    TimePeriod={"Start": today, "End": today},
    Granularity="DAILY",
    Metrics=["UnblendedCost"]
)

amount = cost["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]

# Generate PDF
file_name = f"/tmp/aws-report-{today}.pdf"

c = canvas.Canvas(file_name, pagesize=letter)

c.drawString(50, 750, "AWS EC2 and Billing Report")
c.drawString(50, 730, f"Date: {today}")

c.drawString(50, 700, "Running Instances:")
y = 680

for inst in instance_ids:
    c.drawString(70, y, inst)
    y -= 20

c.drawString(50, y-20, f"Total Cost: ${amount}")

c.save()

print("PDF created:", file_name)

# Upload to S3
s3.upload_file(file_name, BUCKET, f"reports/aws-report-{today}.pdf")

print("PDF uploaded to S3 successfully")
