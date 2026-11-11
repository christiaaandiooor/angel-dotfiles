#!/usr/bin/env bash
# fecha en español sin necesitar locale es_*
d=(Domingo Lunes Martes Miércoles Jueves Viernes Sábado)
m=(enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre)
echo "${d[$(date +%w)]} $(date +%-d) de ${m[$(( $(date +%-m) - 1 ))]} ♡"
