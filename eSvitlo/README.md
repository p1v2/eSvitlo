This lambda is triggering every minute and checks all DynamoDB records.
If any records has old timestamp and status is on, it sets status off and
sends telegram message, or if status is off but timestamp is recent it sends
telegram message that electricity is on.
