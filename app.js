const express = require('express')
const path = require('path')
const {spawn} = require('child_process')
const multer = require('multer')
const bodyParser = require('body-parser');
const app = express()
const port = 5001

//Global variable to see if at least one file has been uploaded
app.locals.fileIsUpdated = false

// STATIC GENERATION OF HTML PAGE
app.set('view engine', 'pug')

// SET STORAGE FOR FILE UPLOAD
let storage = multer.diskStorage({
    destination: function (req, file, cb) {
      cb(null, './data')
    },
    filename: function (req, file, cb) {
      // cb(null, file.fieldname + '-' + Date.now())
      cb(null, 'uploaded_data.csv')
    }
  })

// UPLOADER which control files extension
let upload = multer({ 
  storage: storage,
  fileFilter: function (req, file, cb) {
    var ext = path.extname(file.originalname);
    if(ext !== '.csv') {
        return cb(new Error('Only .csv are allowed'))
    }
    cb(null, true)
} })

// STATIC PAGES FOR DATA FILES
app.use('/data', express.static(path.join(__dirname, 'data')));

// Useful for checkboxes
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Main Route generate the 'home page' using Pug
app.get('/', (req, res) => {
    res.render('index', { fileIsUpdated: app.locals.fileIsUpdated })
  });


// Post route to upload the file
app.post('/file_upload', upload.single('myFile'), (req, res, next )=>{
    console.log("upload requested")
    const file = req.file
    
    // Check for successfull upload
    if(!file) {
        return res.status(500).render('upload_fail')
    }
    // console.log(file.filename)
    
    // Update global var
    app.locals.fileIsUpdated = true;
    
    // Render success message
    res.render('index', { fileIsUpdated: app.locals.fileIsUpdated, 
                          updateSuccess: 'Upload succeeded'})
})

// Post route to spawn a Python process
// Checks if checkboxes are check or files have been uploaded
app.post('/run', (req, res) => {
    if(req.body['testdata']) {
      console.log('Use test data')
      filename = 'test_data_claim.csv'
    } else if (app.locals.fileIsUpdated){
      console.log('Use uploaded data')
      filename = 'uploaded_data.csv'
    } else {
      console.log('No files uploaded')
      return res.status(500).render('No Uploaded File')
    }

    // Actual spawning, it takes an argument which is the file name
    var dataToSend; 
    const python = spawn('python', ['./scripts/script.py', filename]);
    python.stdout.on('data', (data) => {
        console.log('Piping...');
        dataToSend = data.toString(); 
    });

    // On closing the spawn return the stdout of the python process
    python.on('close', (code)=>{
        console.log('Process Ended');
        console.log(dataToSend)
        res.render  ('result', {dataframeHead: dataToSend})
    });
})

// Simple check to see the app is live
app.listen(port, () => {
  console.log(`Example app listening at http://localhost:${port}`)
})

// Catch all 404 page
app.get('*', function(req, res){
  res.render('404')
})

