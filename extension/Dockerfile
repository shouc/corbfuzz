FROM php:7-apache

RUN docker-php-source extract
COPY . /usr/src/php/ext/hsfuzz

RUN docker-php-ext-install hsfuzz && docker-php-source delete
