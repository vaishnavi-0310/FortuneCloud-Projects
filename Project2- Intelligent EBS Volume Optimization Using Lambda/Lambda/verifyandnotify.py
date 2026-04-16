import boto3
from datetime import datetime, timezone

ec2 = boto3.client("ec2")
sns = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("EBSVolumeLogs")
SNS_TOPIC_ARN = "YOUR_SNS_TOPIC_ARN"

def lambda_handler(event, context):
    results = []

    for vol in event:
        volume_id = vol["VolumeId"]

        mod = ec2.describe_volumes_modifications(
            VolumeIds=[volume_id]
        )

        mods = mod.get("VolumesModifications", [])

        if mods:
            status = mods[0].get("ModificationState", "unknown")
            progress = mods[0].get("Progress", 0)
            target_type = mods[0].get("TargetVolumeType", "gp3")
        else:
            status = "unknown"
            progress = 0
            target_type = "gp3"

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        table.put_item(
            Item={
                "VolumeId": volume_id,
                "Timestamp": timestamp,
                "InstanceId": vol["InstanceId"],
                "VolumeType": vol["VolumeType"],
                "Size": str(vol["Size"]),
                "Region": vol["Region"],
                "Status": status,
                "TargetType": target_type,
                "Progress": str(progress)
            }
        )

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="EBS Volume Converted",
            Message=(
                f"Volume ID: {volume_id}\n"
                f"Instance ID: {vol['InstanceId']}\n"
                f"Region: {vol['Region']}\n"
                f"Old Type: {vol['VolumeType']}\n"
                f"Target Type: {target_type}\n"
                f"Status: {status}\n"
                f"Progress: {progress}%\n"
                f"Timestamp: {timestamp}"
            )
        )

        results.append({
            "VolumeId": volume_id,
            "Status": status,
            "Progress": progress
        })

    print(f"Verified and notified for {len(results)} volumes")
    return results
