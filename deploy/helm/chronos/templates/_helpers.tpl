{{- define "chronos.image" -}}
{{ .Values.image.repository }}:{{ required "image.tag is required (commit SHA)" .Values.image.tag }}
{{- end }}

{{- define "chronos.labels" -}}
app.kubernetes.io/name: chronos
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "chronos.selector" -}}
app.kubernetes.io/name: chronos
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{- define "chronos.podSecurity" -}}
securityContext:
  runAsNonRoot: true
  seccompProfile:
    type: RuntimeDefault
{{- end }}

{{- define "chronos.containerSecurity" -}}
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: [ALL]
{{- end }}

{{/* The migration Job as hook (upgrade) or as plain resource (install), see migrate-job.yaml. */}}
{{- define "chronos.migrateJobSpec" -}}
backoffLimit: {{ .Values.migrate.backoffLimit }}
activeDeadlineSeconds: {{ .Values.migrate.activeDeadlineSeconds }}
template:
  metadata:
    labels:
      {{- include "chronos.selector" (dict "root" $ "component" "migrate") | nindent 6 }}
  spec:
    restartPolicy: Never
    imagePullSecrets:
      - name: {{ .Values.image.pullSecret }}
    {{- include "chronos.podSecurity" . | nindent 4 }}
    containers:
      - name: migrate
        image: {{ include "chronos.image" . }}
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        args: [migrate]
        env:
          - name: DATABASE_URL
            valueFrom:
              secretKeyRef:
                name: {{ .Values.databaseSecret }}
                key: DATABASE_URL
        resources:
          requests: {cpu: 10m, memory: 16Mi}
          limits: {cpu: 200m, memory: 128Mi}
        {{- include "chronos.containerSecurity" . | nindent 8 }}
{{- end }}
