# Lab 15: StatefulSets & Persistent Storage - Submission

**Name:** Maria Nikolashina  
**Date:** 2026-04-21  
**Cluster:** `minikube` on context `lab11`  
**Chart:** `k8s/devops-info-service`

## 1. StatefulSet Overview

I converted the service chart from a Deployment-centric model to a StatefulSet model for the stateful lab scenario.

Why StatefulSet:

- stable pod identities with ordinal names
- per-pod persistent storage through `volumeClaimTemplates`
- ordered creation and replacement semantics
- direct DNS access to each pod through a headless service

Deployment vs StatefulSet:

- Deployment is the right default for stateless replicas that can be replaced in any order
- StatefulSet is the right choice when each replica needs its own identity and its own storage

Typical StatefulSet workloads:

- databases such as PostgreSQL and MySQL
- queues and brokers such as Kafka and RabbitMQ
- clustered systems such as Elasticsearch and Cassandra

Headless service:

- I added a service with `clusterIP: None`
- Kubernetes publishes pod-specific DNS records for the StatefulSet through that service
- the pod DNS pattern is:
  - `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`

## 2. Chart Changes

I added StatefulSet support to the Helm chart while keeping the Deployment and Rollout templates in place for other labs and reference.

Relevant files:

- [StatefulSet template](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/statefulset.yaml)
- [Headless service template](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/service-headless.yaml)
- [Deployment gate update](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/deployment.yaml)
- [PVC gate update](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/pvc.yaml)
- [Template helpers](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/_helpers.tpl)
- [StatefulSet values](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values-lab15-statefulset.yaml)

The StatefulSet template includes:

- `serviceName` pointing to the headless service
- `volumeClaimTemplates` so each pod gets its own PVC
- `updateStrategy` support for both `RollingUpdate` and `OnDelete`

## 3. Resource Verification

Main StatefulSet resource evidence:

- [kubectl get po,sts,svc,pvc output](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/resources.txt)

Observed layout:

```text
pod/devops-info-service-ss-0
pod/devops-info-service-ss-1
pod/devops-info-service-ss-2

statefulset.apps/devops-info-service-ss

service/devops-info-service-ss
service/devops-info-service-ss-headless

persistentvolumeclaim/data-devops-info-service-ss-0
persistentvolumeclaim/data-devops-info-service-ss-1
persistentvolumeclaim/data-devops-info-service-ss-2
```

This confirms the expected StatefulSet behavior:

- ordinal pod names
- one PVC per replica
- a separate headless service for direct pod DNS

## 4. Network Identity

DNS resolution evidence:

- [pod DNS and visit capture](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/pod-visits.txt)

Resolved names:

```text
devops-info-service-ss-1.devops-info-service-ss-headless.lab15-ss.svc.cluster.local -> 10.244.0.80
devops-info-service-ss-2.devops-info-service-ss-headless.lab15-ss.svc.cluster.local -> 10.244.0.81
```

That is the stable StatefulSet DNS pattern the lab asked for.

## 5. Per-Pod Storage Evidence

I accessed each pod through its direct DNS name and incremented the app counter independently.

Evidence:

- [pod DNS and visit capture](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/pod-visits.txt)

Per-pod counts:

```text
devops-info-service-ss-0
  root_count = 1
  visits_count = 1
  storage_file = /data/visits
devops-info-service-ss-1
  root_count = 2
  visits_count = 2
  storage_file = /data/visits
devops-info-service-ss-2
  root_count = 3
  visits_count = 3
  storage_file = /data/visits
```

This shows the storage is isolated per pod rather than shared across the replicas.

## 6. Persistence Test

I deleted pod `devops-info-service-ss-0`, waited for the StatefulSet controller to recreate it, and then checked the persisted counter again.

Evidence:

- [pre-delete count](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/persistence-before.txt)
- [post-recreate count](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/persistence-after.txt)
- [recreated pod status](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/persistence-pod0-after-recreate.txt)

Result:

- before deletion: `visits = 1`
- after recreation: `visits = 1`

The pod IP changed from the original instance to the replacement instance, but the persisted counter stayed the same, which is the important StatefulSet storage guarantee.

## 7. Bonus: Partitioned Rolling Update

I tested a partitioned StatefulSet rollout with `partition: 2`.

Important note:

- the application reads some config values dynamically, so the app-level `service.environment` field is not a reliable rollout marker for this bonus test
- the StatefulSet controller revision hash is the correct source of truth for which pods actually rolled

Evidence:

- [partition baseline resources](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/partition-resources.txt)
- [partition baseline revision hashes](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/partition-revisions.txt)

After upgrading the template, the pod revisions were:

```text
devops-info-service-partition-0 => devops-info-service-partition-578fff78c9
devops-info-service-partition-1 => devops-info-service-partition-578fff78c9
devops-info-service-partition-2 => devops-info-service-partition-948f96f7d
```

That confirms only ordinal `2` moved to the new controller revision, which matches the configured partition.

Relevant files:

- [partition values](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values-lab15-partition.yaml)
- [partition revision evidence](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/partition-revisions.txt)

## 8. Bonus: OnDelete Strategy

I also tested `updateStrategy.type: OnDelete`.

Behavior:

- upgrading the StatefulSet template did not restart any pod immediately
- after I manually deleted one pod, only that pod was recreated on the new revision

Evidence:

- [OnDelete baseline resources](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/ondelete-resources.txt)
- [OnDelete baseline revisions](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/ondelete-before-revisions.txt)
- [OnDelete after upgrade revisions](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/ondelete-after-upgrade-revisions.txt)
- [OnDelete after delete revisions](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/ondelete-after-delete-revisions.txt)
- [OnDelete after delete pod state](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/ondelete-after-delete-pods.txt)

Observed revision hashes:

Before delete:

```text
devops-info-service-ondelete-0   devops-info-service-ondelete-74f87577
devops-info-service-ondelete-1   devops-info-service-ondelete-74f87577
devops-info-service-ondelete-2   devops-info-service-ondelete-74f87577
```

After deleting pod `1`:

```text
devops-info-service-ondelete-0   devops-info-service-ondelete-74f87577
devops-info-service-ondelete-1   devops-info-service-ondelete-5748595776
devops-info-service-ondelete-2   devops-info-service-ondelete-74f87577
```

That is the expected OnDelete behavior: nothing rolls until a pod is deleted manually.

Relevant files:

- [OnDelete values](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values-lab15-ondelete.yaml)
- [OnDelete revision evidence](/Users/marianikolashina/DevOps-Core-Course/k8s/evidence/lab15/ondelete-after-delete-revisions.txt)

## 9. Files Changed

- [Chart values](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values.yaml)
- [Template helpers](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/_helpers.tpl)
- [Deployment template gate](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/deployment.yaml)
- [PVC template gate](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/pvc.yaml)
- [Headless service template](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/service-headless.yaml)
- [StatefulSet template](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/templates/statefulset.yaml)
- [Lab 15 StatefulSet values](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values-lab15-statefulset.yaml)
- [Lab 15 partition values](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values-lab15-partition.yaml)
- [Lab 15 OnDelete values](/Users/marianikolashina/DevOps-Core-Course/k8s/devops-info-service/values-lab15-ondelete.yaml)
- [Lab 15 report](/Users/marianikolashina/DevOps-Core-Course/k8s/STATEFULSET.md)
