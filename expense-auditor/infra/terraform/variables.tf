variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "fastapi-app"
}

variable "environment" {
  description = "Deployment environment (e.g., dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "container_image" {
  description = "Docker image for the application"
  type        = string
  default     = "your-ecr-repo/fastapi-app:latest"
}

variable "container_port" {
  description = "Port the container exposes"
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Number of instances of the task to run"
  type        = number
  default     = 1
}

variable "cpu" {
  description = "CPU units for the task (1 vCPU = 1024 units)"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Memory for the task in MiB"
  type        = number
  default     = 512
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
  default     = ""
  sensitive   = true
}

variable "celery_broker_url" {
  description = "Celery broker connection URL"
  type        = string
  default     = ""
  sensitive   = true
}
