#!/usr/bin/env sh
#
#: Title        : update-requirements-description.sh
#: Date         : 26-Sep-2020
#: Version      : 0.1
#: Description  : This script will print out a file after
#                 replacing a certain placeholder text in
#                 the file with the content from the
#                 'requirements.txt' file which is downloaded
#                 from the Archivy repository on Github.
#                 
#: Options      : Accepts two. First is the placeholder text
#                 in the file. Second is the name of the file
#                 in which the text is to be replaced.
#: Usage        : Call the script and pass the placeholder text
#                 and filename as arguments to it.
#                 Example:
#                 ./update-requirements-description.sh "%text%" "README.md"
################


# Function used to download 'requirements.txt' file from master branch
# Usage: Calling this function will download the 'requirements.txt' from
#        the URL defined within the function.
#
getRequirementsFile() {
  # Variable that points to file's URL
  local requirementsFileUrl="https://raw.githubusercontent.com/Uzay-G/archivy/master/requirements.txt"

  # If wget is present
  if [ "$(command -v wget)" ] ; then
    # Download the file
    wget -qc "${requirementsFileUrl}" -O ./requirements.txt || (printf '%s\n' "Could not download file from \"${requirementsFileUrl}\"." 1>&2 ; exit 1)
  # If cURL is present
  elif [ "$(command -v curl)" ] ; then
    curl "${requirementsFileUrl}" --output ./requirements.txt || (printf '%s\n' "Could not download file from \"${requirementsFileUrl}\"." 1>&2 ; exit 1)
  else
    printf '%s\n' "Please install either wget or curl. Required for fetching requirements.txt file." 1>&2
    exit 1
  fi
}


# Function used to check if requirements.txt file is present
#
# Input  :  No inputs necessary
# Output :  Prints out the full path to the 'requirements.txt' file
#
checkIfPresent() {
  local requirementsFilePath="./requirements.txt"

  # If file is present and is not empty
  if [ -s "${requirementsFilePath}" ] ; then
    # Get full path of file and print the path
    filePath="$(readlink -f "${requirementsFilePath}")" \
      && echo "${filePath}"
  else
    printf '%s\n' "Could not find \"${requirementsFilePath}\" in \"${PWD}\"." \
      && exit 1
  fi
}


# Function used to filter out comments from 'requirements.txt' file
#
# Input  :  Expects path to 'requirements.txt' file
# Output :  Prints out the file without any comments (lines beginning with '#')
#
filterComments() {
  # If one argument is provided and it is not an empty string
  if [ $# -eq 1 ] && [ "$1" != "" ] ; then
    local filePath="$1"
    
    # If file exists and is not empty
    if [ -s "${filePath}" ] ; then
      # Filter out any empty lines and comments(lines beginning with '#')
      grep -Ev "^#|^$" "${filePath}" | sed -e 's/^/\*\ `/;s/$/`/'
    fi
  else
    printf '%s\n' "Provide full path to requirements.txt file. Incorrect argument received." 1>&2 \
      && exit 1
  fi
}


# Function used to replace placeholder text
# 
# Input  :  Takes two arguments. First one is the placeholder text which
#           is to be replaced. The second one is the name of the file in
#           which the placeholder is to be replaced.
#
# Output :  Prints text after the placeholder text has been replaced. This
#           DOES NOT modify the file given as input to the function. To
#           modify the file, you will need to redirect the output of this
#           function to the file itself.
#
replacePlaceholder() {
  # If two arguments are given, and if the first argument is not an empty string
  # and if the second argument points to a non-empty file that exists 
  if [ $# -eq 2 ] && [ "$1" != "" ] && [ -s "$(readlink -f "$2")" ] ; then
    local placeholderText="$1"
    local replaceInFile="$( readlink -f "$2")"
  # If file does not exist or is empty
  elif [ ! -s "$(readlink -f "$2")" ] ; then
    printf '%s\n' "Could not find ${replaceInFile} in ${PWD}." 1>&2 \
      && exit 1
  else
    printf '%s\n' "Incorrect arguments. Or $2 does not exist." \
      && exit 1
  fi

  # If the placeholder text could not be found in the file
  if [ "$(grep -o "${placeholderText}" "${replaceInFile}")" == "" ] ; then
    printf '%s\n' "${replaceInFile} did not contain \"${placeholderText}\"." 1>&2 \
      && exit 1
  fi

  # Pass the path to the 'requirements.txt' as an argument to the filterComments function
  # The output of this will be the filtered and formatted text which is assigned to a variable
  replaceWith="$(filterComments "$(checkIfPresent)")"

  # The below one-liner prints out the contents of the file after replacing the placeholder text
  gawk -v r="${replaceWith}" "{gsub(/"${placeholderText}"/,r)}1" Docker-test.md \
    || (printf '%s\n' "Could not replace \"${placeholderText}\" in \"${replaceInFile}\"." 1>&2 && exit 1)
}


# Main function
#
main() {
  if [ $# -eq 2 ] && [ "$1" != "" ] && [ -s "$(readlink -f "$2")" ] ; then
    # Store placeholder text and path to file
    local placeholderText="$1"
    local replaceFile="$2"

    # Fetch the 'requirements.txt' file
      # Check if the 'requirements.txt' file is present in the current working directory 
      # and pass the output of the function as an argument to the 'filterComments' function
    getRequirementsFile \
      && replacePlaceholder "${placeholderText}" "${replaceFile}"
  else
    printf '%s\n' "Incorrect arguments given. Expecting two arguments. First is the placeholder text. Second is the path to the file." 1>&2 \
      && exit 1
  fi
}


# Function used to cleanup after.
# This function deletes the 'requirements.txt' file
#
cleanup() {
  # Remove file 
  rm "$(checkIfPresent)"
}

# Trapping signals
trap cleanup 0 1 2 3 5 15

# Calling the 'main' function
main "$@"

# End of script
