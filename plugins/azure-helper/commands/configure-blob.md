# /configure-blob - Configure Azure Blob Storage

Create and configure an Azure Blob Storage account with security best practices.

## Steps

1. Ask the user for the storage purpose: files, backups, media, static hosting, data lake
2. Choose the performance tier: Standard (HDD) or Premium (SSD) based on workload
3. Select the redundancy: LRS, ZRS, GRS, or RA-GRS based on availability requirements
4. Create the storage account with the selected configuration
5. Create blob containers with appropriate access levels (private, blob, container)
6. Configure encryption: Microsoft-managed or customer-managed keys
7. Set up lifecycle management policies for tiering and deletion
8. Configure network security: private endpoints, firewall rules, VNet integration
9. Enable soft delete for blob and container recovery (default 7 days)
10. Set up Azure CDN integration for static content delivery if needed
11. Generate the Bicep or ARM template for the storage configuration
12. Document: account name, containers, access policies, lifecycle rules, network settings

## Rules

- Default to private access level for all containers
- Enable soft delete for accidental deletion recovery
- Use private endpoints for storage accessed from VNets
- Configure lifecycle policies to move infrequently accessed data to cool/archive tiers
- Enable blob versioning for data protection
- Use Azure AD authentication over access keys when possible
- Set up immutability policies for compliance-required data
