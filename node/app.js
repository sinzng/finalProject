const express = require('express');
const morgan = require('morgan');
const path = require('path');
const app = express();
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const cors = require('cors');

// 라우터 import
const routes = require('./routes/main');

app.set('port', 8000);
app.use(morgan('dev'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));
app.use(cors());

// 라우터 사용
app.use('/', routes);

app.listen(app.get('port'), () => {
    console.log("8000 Port: Server Started~!!");
});