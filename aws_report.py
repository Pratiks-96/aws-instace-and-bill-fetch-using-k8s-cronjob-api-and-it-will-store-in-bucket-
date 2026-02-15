import boto3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
import os

# Read environment variables
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

# Cost Explorer only works in us-east-1 region
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

# ----------------------------
# Fetch EC2 Instance Details
# ----------------------------
print("Fetching EC2 instance details...")

instances = ec2.describe_instances()

instance_details = []

for reservation in instances["Reservations"]:
    for instance in reservation["Instances"]:
        instance_id = instance["InstanceId"]
        state = instance["State"]["Name"]

        # Get instance name tag if exists
        name = "N/A"
        if "Tags" in instance:
            for tag in instance["Tags"]:
                if tag["Key"] == "Name":
                    name = tag["Value"]

        instance_details.append({
            "InstanceId": instance_id,
            "Name": name,
            "State": state
        })

# ----------------------------
# Fetch Billing Information
# ----------------------------
print("Fetching billing details...")

today = datetime.utcnow().date()
yesterday = today - timedelta(days=1)

start_date = yesterday.strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")

cost_response = ce.get_cost_and_usage(
    TimePeriod={
        "Start": start_date,
        "End": end_date
    },
    Granularity="DAILY",
    Metrics=["UnblendedCost"]
)

amount = cost_response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
unit = cost_response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Unit"]

# ----------------------------
# Generate PDF
# ----------------------------
print("Generating PDF report...")

report_date = today.strftime("%Y-%m-%d")
file_name = f"/tmp/aws-report-{report_date}.pdf"

c = canvas.Canvas(file_name, pagesize=letter)

c.setFont("Helvetica", 12)

c.drawString(50, 750, "AWS EC2 and Billing Report")
c.drawString(50, 730, f"Report Date: {report_date}")

# Instance section
c.drawString(50, 700, "EC2 Instance Details:")

y_position = 680

if len(instance_details) == 0:
    c.drawString(70, y_position, "No instances found")
else:
    for inst in instance_details:
        text = f"ID: {inst['InstanceId']} | Name: {inst['Name']} | State: {inst['State']}"
        c.drawString(70, y_position, text)
        y_position -= 20

# Billing section
y_position -= 20
c.drawString(50, y_position, "Billing Details:")

y_position -= 20
c.drawString(70, y_position, f"Cost ({start_date}): {amount} {unit}")

c.save()

print(f"PDF created successfully: {file_name}")

# ----------------------------
# Upload to S3
# ----------------------------
print("Uploading PDF to S3...")

s3_key = f"reports/aws-report-{report_date}.pdf"

s3.upload_file(file_name, BUCKET, s3_key)

print(f"PDF uploaded successfully to S3 bucket: {BUCKET}/{s3_key}")

print("Job completed successfully.")
