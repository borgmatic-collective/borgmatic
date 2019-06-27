FROM python:3.7.3-alpine3.10 as borgmatic

COPY . /app
RUN pip install --no-cache /app && generate-borgmatic-config && chmod +r /etc/borgmatic/config.yaml
RUN borgmatic --help > /command-line.txt \
    && for action in init prune create check extract list info; do \
           echo -e "\n--------------------------------------------------------------------------------\n" >> /command-line.txt \
           && borgmatic "$action" --help >> /command-line.txt; done

FROM node:12.4.0-alpine as html

WORKDIR /source

RUN npm install @11ty/eleventy \
    @11ty/eleventy-plugin-syntaxhighlight \
    @11ty/eleventy-plugin-inclusive-language \
    markdown-it \
    markdown-it-anchor \
    markdown-it-replace-link
COPY --from=borgmatic /etc/borgmatic/config.yaml /source/docs/_includes/borgmatic/config.yaml
COPY --from=borgmatic /command-line.txt /source/docs/_includes/borgmatic/command-line.txt
COPY . /source
RUN npx eleventy --input=/source/docs --output=/output/docs \
  && mv /output/docs/index.html /output/index.html

FROM nginx:1.16.0-alpine

COPY --from=html /output /usr/share/nginx/html
COPY --from=borgmatic /etc/borgmatic/config.yaml /usr/share/nginx/html/docs/reference/config.yaml
