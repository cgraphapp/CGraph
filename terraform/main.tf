terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
  
  backend "s3" {
    bucket         = "cgraph-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "CGRAPH"
      ManagedBy   = "Terraform"
    }
  }
}

provider "kubernetes" {
  host                   = aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority.data)
  token                  = data.aws_eks_cluster_auth.main.token
}

provider "helm" {
  kubernetes {
    host                   = aws_eks_cluster.main.endpoint
    cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority.data)
    token                  = data.aws_eks_cluster_auth.main.token
  }
}

# EKS Cluster
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = var.cluster_name
  cluster_version = "1.27"
  
  vpc_id             = aws_vpc.main.id
  subnet_ids         = aws_subnet.private[*].id
  
  node_groups = {
    main = {
      desired_size = 3
      min_size     = 3
      max_size     = 10
      
      instance_types = ["t3.large"]
      disk_size      = 50
      
      labels = {
        role = "general"
      }
    }
    
    compute = {
      desired_size = 2
      min_size     = 2
      max_size     = 5
      
      instance_types = ["t3.xlarge"]
      disk_size      = 100
      
      labels = {
        role = "compute"
      }
    }
  }
  
  enable_cluster_autoscaler = true
  enable_metrics_server     = true
}

# RDS PostgreSQL
module "rds" {
  source = "./modules/rds"
  
  identifier = "cgraph-postgres"
  engine     = "postgres"
  engine_version = "15.2"
  
  allocated_storage = 100
  max_allocated_storage = 1000
  storage_encrypted = true
  
  instance_class = "db.r6i.xlarge"
  
  db_name  = "cgraph"
  username = "cgraph_admin"
  password = random_password.db_password.result
  
  multi_az = true
  storage_type = "gp3"
  iops     = 3000
  
  backup_retention_period = 30
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"
  
  enable_cloudwatch_logs_exports = ["postgresql"]
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
}

# Redis Cluster
module "redis" {
  source = "./modules/elasticache"
  
  cluster_id           = "cgraph-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.r6g.xlarge"
  num_cache_nodes      = 3
  parameter_group_name = "default.redis7"
  
  automatic_failover_enabled = true
  multi_az_enabled           = true
  
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_token.result
  at_rest_encryption_enabled = true
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
}

# Load Balancer
resource "aws_lb" "main" {
  name               = "cgraph-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  
  enable_deletion_protection = true
  enable_http2               = true
  enable_cross_zone_load_balancing = true
  
  tags = {
    Name = "CGRAPH ALB"
  }
}

# Outputs
output "eks_cluster_endpoint" {
  value       = module.eks.cluster_endpoint
  description = "EKS cluster endpoint"
}

output "rds_endpoint" {
  value       = module.rds.db_instance_endpoint
  description = "RDS database endpoint"
  sensitive   = true
}

output "redis_endpoint" {
  value       = module.redis.cluster_address
  description = "Redis cluster endpoint"
  sensitive   = true
}