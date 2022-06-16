FROM alpine:3.16.0 as borgmatic

COPY . /app
RUN apk add --no-cache py3-pip py3-ruamel.yaml py3-ruamel.yaml.clib
RUN pip install --no-cache /app && generate-borgmatic-config && chmod +r /etc/borgmatic/config.yaml
RUN borgmatic --help > /command-line.txt \
    && for action in init prune compact create check extract export-tar mount umount restore list info borg; do \
           echo -e "\n--------------------------------------------------------------------------------\n" >> /command-line.txt \
           && borgmatic "$action" --help >> /command-line.txt; done

FROM node:18.4.0-alpine as html

ARG ENVIRONMENT=production

WORKDIR /source

RUN npm install @11ty/eleventy \
    @11ty/eleventy-plugin-syntaxhighlight \
    @11ty/eleventy-plugin-inclusive-language \
    @11ty/eleventy-navigation \
    markdown-it \
    markdown-it-anchor \
    markdown-it-replace-link
COPY --from=borgmatic /etc/borgmatic/config.yaml /source/docs/_includes/borgmatic/config.yaml
COPY --from=borgmatic /command-line.txt /source/docs/_includes/borgmatic/command-line.txt
COPY . /source
RUN NODE_ENV=${ENVIRONMENT} npx eleventy --input=/source/docs --output=/output/docs \
  && mv /output/docs/index.html /output/index.html

FROM nginx:1.22.0-alpine

COPY --from=html /output /usr/share/nginx/html
COPY --from=borgmatic /etc/borgmatic/config.yaml /usr/share/nginx/html/docs/reference/config.yaml
