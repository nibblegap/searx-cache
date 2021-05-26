module.exports = function(grunt) {

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    uglify: {
      dist: {
        files: {
          'js/eelo.min.js': ['js/eelo.js']
        }
      }
    },
    jshint: {
      files: ['gruntfile.js', 'js/eelo.js'],
      options: {
        reporterOutput: "",
        // options here to override JSHint defaults
        globals: {
          jQuery: true,
          console: true,
          module: true,
          document: true
        }
      }
    },
    less: {
        development: {
            options: {
                paths: ["less/eelo"]
                //banner: '/*! less/eelo/oscar.css | <%= grunt.template.today("dd-mm-yyyy") %> | https://github.com/asciimoo/searx */\n'
            },
            files: {"css/eelo.css": "less/eelo/eelo.less"}
        },
        production: {
            options: {
                paths: ["less/eelo"],
                //banner: '/*! less/eelo/oscar.css | <%= grunt.template.today("dd-mm-yyyy") %> | https://github.com/asciimoo/searx */\n',
                cleancss: true
            },
            files: {"css/eelo.min.css": "less/eelo/eelo.less"}
        },
        /*
        // built with ./manage.sh styles
        bootstrap: {
            options: {
                paths: ["less/bootstrap"],
                cleancss: true
            },
            files: {"css/bootstrap.min.css": "less/bootstrap/bootstrap.less"}
        },
        */
    },
    watch: {
        scripts: {
            files: ['<%= jshint.files %>'],
            tasks: ['jshint', 'uglify']
        },
        eelo_styles: {
            files: ['less/eelo/**/*.less'],
            tasks: ['less:development', 'less:production']
        },
        bootstrap_styles: {
            files: ['less/bootstrap/**/*.less'],
            tasks: ['less:bootstrap']
        }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-less');

  grunt.registerTask('test', ['jshint']);

  grunt.registerTask('default', ['jshint', 'uglify', 'less']);

  grunt.registerTask('styles', ['less']);

};
