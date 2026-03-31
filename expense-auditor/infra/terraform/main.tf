terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    # Configure these values in a separate backend.tfvars file
    # bucket         = "your-terraform-state-bucket"
    # key            = "your-app/terraform.tfstate"
    # region         = "us-west-2"
    # dynamodb_table = "terraform-locks"
    # encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "Terraform"
    }
  }
}

# Create VPC and networking resources
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${var.project_name}-${var.environment}"
  cidr = var.vpc_cidr
  
  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  enable_nat_gateway     = true
  single_nat_gateway     = var.environment != "production"
  one_nat_gateway_per_az = var.environment == "production"
  
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

# Create ECS cluster and service
module "ecs" {
  source = "./modules/ecs"
  
  project_name  = var.project_name
  environment   = var.environment
  vpc_id        = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnets
  private_subnets = module.vpc.private_subnets
  
  container_image = var.container_image
  container_port  = var.container_port
  
  desired_count   = var.desired_count
  cpu             = var.cpu
  memory          = var.memory
  
  # Environment variables for the container
  environment_variables = [
    {
      name  = "DATABASE_URL"
      value = var.database_url
    },
    {
      name  = "CELERY_BROKER_URL"
      value = var.celery_broker_url
    },
    {
      name  = "ENVIRONMENT"
      value = var.environment
    }
  ]
  
  # Secrets from AWS Secrets Manager
  secrets = [
    {
      name      = "SECRET_KEY"
      valueFrom = aws_secretsmanager_secret.app_secrets.arn
    }
  ]
}

# Create a secret for the application
resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${var.project_name}-${var.environment}-secrets"
  description = "Secrets for ${var.project_name} application in ${var.environment} environment"
  
  tags = {
    Name = "${var.project_name}-${var.environment}-secrets"
  }
}

# Example secret value (in production, set these externally)
resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id     = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    SECRET_KEY = "change-me-in-production"
  })
}

# Create CloudWatch log group
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/ecs/${var.project_name}-${var.environment}"
  retention_in_days = 30
  
  tags = {
    Name = "${var.project_name}-${var.environment}-logs"
  }
}
