{{/*
Expand the chart name.
*/}}
{{- define "devops-info-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "devops-info-service.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create chart label.
*/}}
{{- define "devops-info-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Selector labels.
*/}}
{{- define "devops-info-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-info-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: web
{{- end -}}

{{/*
Common labels.
*/}}
{{- define "devops-info-service.labels" -}}
helm.sh/chart: {{ include "devops-info-service.chart" . }}
{{ include "devops-info-service.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: devops-core-course
{{- end -}}

{{/*
Create the ServiceAccount name.
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "devops-info-service.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
Create the ConfigMap name used for the mounted config file.
*/}}
{{- define "devops-info-service.configFileMapName" -}}
{{- printf "%s-config" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create the ConfigMap name used for envFrom injection.
*/}}
{{- define "devops-info-service.configEnvMapName" -}}
{{- printf "%s-env" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create the PVC name for persistent application data.
*/}}
{{- define "devops-info-service.pvcName" -}}
{{- if .Values.persistence.existingClaim -}}
{{- .Values.persistence.existingClaim | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-data" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Create the preview service name used by blue-green rollouts.
*/}}
{{- define "devops-info-service.previewServiceName" -}}
{{- printf "%s-preview" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create the Secret name.
*/}}
{{- define "devops-info-service.secretName" -}}
{{- if .Values.secrets.nameOverride -}}
{{- .Values.secrets.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-secret" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Render common non-sensitive environment variables.
*/}}
{{- define "devops-info-service.commonEnv" -}}
- name: HOST
  value: {{ .Values.env.host | quote }}
- name: PORT
  value: {{ .Values.env.port | quote }}
- name: APP_ENV
  value: {{ .Values.env.appEnv | quote }}
- name: APP_REVISION
  value: {{ .Values.env.appRevision | quote }}
- name: CONFIG_FILE
  value: {{ printf "%s/%s" .Values.config.mountPath .Values.config.fileName | quote }}
- name: VISITS_FILE
  value: {{ printf "%s/%s" .Values.persistence.mountPath .Values.persistence.fileName | quote }}
{{- with .Values.env.extra }}
{{- range . }}
- name: {{ .name }}
  value: {{ .value | quote }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
Render Kubernetes Secret-backed environment variables.
*/}}
{{- define "devops-info-service.secretEnv" -}}
- name: APP_USERNAME
  valueFrom:
    secretKeyRef:
      name: {{ include "devops-info-service.secretName" . }}
      key: username
- name: APP_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "devops-info-service.secretName" . }}
      key: password
{{- end -}}

{{/*
Render the Vault Agent template that writes a .env-style file.
*/}}
{{- define "devops-info-service.vaultAgentTemplate" -}}
{{`{{- with secret "`}}{{ .Values.vault.secretPath }}{{`" -}}`}}
APP_USERNAME={{`{{ .Data.data.username }}`}}
APP_PASSWORD={{`{{ .Data.data.password }}`}}
{{`{{- end }}`}}
{{- end -}}
