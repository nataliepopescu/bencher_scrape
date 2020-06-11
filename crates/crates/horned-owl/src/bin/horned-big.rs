use clap::App;
use clap::Arg;
use clap::ArgMatches;

use failure::Error;

use horned_owl::io::writer::write;
use horned_owl::model::Build;
use horned_owl::model::Ontology;

use std::io::stdout;

fn main() -> Result<(), Error> {
    let matches = App::new("horned-big")
        .version("0.1")
        .about("Generate a big OWL file for testing")
        .author("Phillip Lord")
        .arg(
            Arg::with_name("SIZE")
                .help("The number of classes the file should have")
                .required(true)
                .index(1),
        )
        .get_matches();

    matcher(matches)
}

fn matcher(matches: ArgMatches) -> Result<(), Error> {
    let size: isize = matches.value_of("SIZE").unwrap().parse()?;

    let b = Build::new();
    let mut o = Ontology::new();

    for i in 1..size {
        o.declare(b.class(format!("https://www.example.com/o{}", i)));
    }

    write(&mut stdout(), &o, None)
}
