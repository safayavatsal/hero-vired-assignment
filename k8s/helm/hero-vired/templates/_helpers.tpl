{{/* Chart name, labels, and stable component names. */}}
{{- define "hero-vired.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "hero-vired.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "hero-vired.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "hero-vired.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "hero-vired.labels" -}}
helm.sh/chart: {{ include "hero-vired.chart" . }}
app.kubernetes.io/name: {{ include "hero-vired.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "hero-vired.selectorLabels" -}}
app.kubernetes.io/name: {{ include "hero-vired.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "hero-vired.secretName" -}}
{{- printf "%s-secrets" (include "hero-vired.fullname" .) -}}
{{- end -}}
