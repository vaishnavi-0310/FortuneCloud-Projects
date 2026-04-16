import boto3

ec2 = boto3.client("ec2")

def lambda_handler(event, context):
    response = ec2.describe_volumes(
        Filters=[
            {"Name": "volume-type", "Values": ["gp2"]},
            {"Name": "tag:AutoConvert", "Values": ["true"]}
        ]
    )

    result = []

    for vol in response.get("Volumes", []):
        result.append({
            "VolumeId": vol["VolumeId"],
            "Size": vol["Size"],
            "VolumeType": vol["VolumeType"],
            "Region": ec2.meta.region_name,
            "InstanceId": vol["Attachments"][0]["InstanceId"] if vol.get("Attachments") else "None"
        })

    print(f"Found {len(result)} matching volumes")

    return result
