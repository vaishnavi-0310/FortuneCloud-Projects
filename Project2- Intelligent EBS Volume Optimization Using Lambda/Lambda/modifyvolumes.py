import boto3

ec2 = boto3.client("ec2")

def lambda_handler(event, context):
    results = []

    for vol in event:
        volume_id = vol["VolumeId"]

        ec2.modify_volume(
            VolumeId=volume_id,
            VolumeType="gp3"
        )

        results.append({
            "VolumeId": volume_id,
            "InstanceId": vol["InstanceId"],
            "Size": vol["Size"],
            "VolumeType": vol["VolumeType"],
            "Region": vol["Region"],
            "Status": "ModificationStarted"
        })

    print(f"Started modification for {len(results)} volumes")
    return results
