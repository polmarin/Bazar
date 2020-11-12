# Bazar
The ultimate website ready to save money on Black Friday (or whenever, really).

## Motivation
I'm desperately needed for a new monitor. I've been coding on a laptop all my life but I'm in need of more screen real state, that's why I'm looking for a nice setup. There's two options: a dual monitor station or just one ultrawide. For whatever reason, I chose the second one and, since Black Friday is close, I wanted to take advantage of it.

I decided to create this simple web-app, which runs a headless Selenium on the background and constantly checks the prices of the products I'm interested in. This way, I can know when a price drops and I can also keep track of the price evolution until November 27th.

## How it works
Since some friends wanted to use it too, I created a user-based system. Each user has to log in and save their search terms in a database (this project has been deployed to Heroku so it's using PostgreSQL there). Then, four times a day, the scraper does its thing and store results in a database too. 
There's a simple graphic interface which shows, in table format, some of the best products obtained (cheapest, biggest sales, best rated...).

This is a really simple project, aimed to be used for personal purposes, but let's it gets me a cheap monitor!
