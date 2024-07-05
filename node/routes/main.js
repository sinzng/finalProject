const express = require("express");
const bodyParser = require("body-parser");
const axios = require("axios");
const JH_IP = process.env.JH_IP_ADDRESS
const SY_IP = process.env.SY_IP_ADDRESS;
const app = express();

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

module.exports = app;