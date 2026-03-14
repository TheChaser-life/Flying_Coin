#!/bin/bash

cd terraform
terraform destroy -target=module.kubernetes -target=module.networking.google_compute_router_nat.nat
