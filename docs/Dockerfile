FROM docker.io/alpine:3.20.1 AS borgmatic

COPY . /app
RUN apk add --no-cache py3-pip py3-ruamel.yaml py3-ruamel.yaml.clib
RUN pip install --break-system-packages --no-cache /app && borgmatic config generate && chmod +r /etc/borgmatic/config.yaml
RUN borgmatic --help > /command-line.txt \
    && for action in repo-create transfer create prune compact check delete extract config "config bootstrap" "config generate" "config validate" export-tar mount umount repo-delete restore repo-list list repo-info info break-lock "key export" "key import" "key change-passphrase" recreate borg; do \
           echo -e "\n--------------------------------------------------------------------------------\n" >> /command-line.txt \
           && borgmatic $action --help >> /command-line.txt; done
RUN /app/docs/fetch-contributors >> /contributors.html

FROM docker.io/node:22.4.0-alpine AS html

ARG ENVIRONMENT=production

WORKDIR /source

RUN npm install @11ty/eleventy \
    @11ty/eleventy-plugin-syntaxhighlight \
    @11ty/eleventy-plugin-inclusive-language \
    @11ty/eleventy-navigation \
    eleventy-plugin-code-clipboard \
    markdown-it \
    markdown-it-anchor \
    markdown-it-replace-link
COPY --from=borgmatic /etc/borgmatic/config.yaml /source/docs/_includes/borgmatic/config.yaml
COPY --from=borgmatic /command-line.txt /source/docs/_includes/borgmatic/command-line.txt
COPY --from=borgmatic /contributors.html /source/docs/_includes/borgmatic/contributors.html
COPY . /source
RUN NODE_ENV=${ENVIRONMENT} npx eleventy --input=/source/docs --output=/output/docs \
  && mv /output/docs/index.html /output/index.html

FROM docker.io/nginx:1.26.1-alpine

COPY --from=html /output /usr/share/nginx/html
COPY --from=borgmatic /etc/borgmatic/config.yaml /usr/share/nginx/html/docs/reference/config.yaml
