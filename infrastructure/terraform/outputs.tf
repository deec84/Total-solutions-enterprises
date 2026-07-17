output "api_base_url" {
  value = "https://${aws_cloudfront_distribution.api.domain_name}"
}

output "ecs_cluster" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service" {
  value = aws_ecs_service.api.name
}

output "ecs_network_configuration" {
  description = "JSON value for the GitHub ECS_NETWORK_CONFIGURATION environment variable."
  value = jsonencode({
    awsvpcConfiguration = {
      subnets        = aws_subnet.private[*].id
      securityGroups = [aws_security_group.api.id]
      assignPublicIp = "DISABLED"
    }
  })
}

output "origin_load_balancer_dns_name" {
  value = aws_lb.api.dns_name
}

output "database_endpoint" {
  value     = aws_db_instance.main.endpoint
  sensitive = true
}

output "media_bucket" {
  value = aws_s3_bucket.media.id
}

output "alarm_topic_arn" {
  value = aws_sns_topic.alarms.arn
}

output "operations_dashboard" {
  value = aws_cloudwatch_dashboard.operations.dashboard_name
}
