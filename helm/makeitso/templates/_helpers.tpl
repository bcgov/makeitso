{{/*
Expand the name of the chart.
*/}}
{{- define "makeitso.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "makeitso.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "makeitso.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "makeitso.labels" -}}
helm.sh/chart: {{ include "makeitso.chart" . }}
{{ include "makeitso.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "makeitso.selectorLabels" -}}
app.kubernetes.io/name: {{ include "makeitso.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "makeitso.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "makeitso.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Environment shared by the app
*/}}
{{- define "makeitso.appEnv" -}}
- name: MAKEITSO_ENV
  value: {{ .Values.app.env | default "prod" }}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: makeitso-db-pguser-postgres
      key: uri
- name: REDIS_URL
  value: redis://{{ include "makeitso.fullname" . }}-redis.{{ .Release.Namespace }}.svc.cluster.local:6379
- name: SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "makeitso.fullname" . }}-secret
      key: appSecretKey
- name: GITHUB_APP_CLIENT_ID
  valueFrom:
    secretKeyRef:
      name: {{ .Values.app.secretName }}
      key: clientId
- name: GITHUB_APP_CLIENT_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ .Values.app.secretName }}
      key: clientSecret
{{- end }}
