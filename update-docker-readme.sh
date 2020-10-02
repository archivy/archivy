#!/usr/bin/env sh
#
#: Title        : update-docker-readme.sh
#: Date         : 26-Sep-2020
#: Version      : 0.1
#: Description  : This script will print out a file after
#                 replacing a certain placeholder text in
#                 the file with the content from the
#                 'requirements.txt' file which is downloaded
#                 from the Archivy repository on Github.
#                 
#: Options      : Requires three. First is the URL to the file whose
#                 contents are to be added. Second is the placeholder
#                 string in the template file. Third is the path to the
#                 template file which contains the placeholder.
#: Usage        : Call the script and pass the placeholder text
#                 and filename as arguments to it.
#                 Example:
#                 ./update-requirements-description.sh "https://link/to/file.txt" \
#                 '%text%' "README-template.md"
################


# Function used to download 'requirements.txt' file from master branch
#
# Input  :  Requires two arguments. First is the URL at which the raw file
#           is available for download. Second is the name with which the
#           downloaded file should be saved as.
# Output :  Prints out the full path to the downloaded file.
#
# Usage  :  Call this function with the first argument being the download link
#           to the file, and the second argument being the name with which the
#           file should be saved.
#           Example:
#                  getFile "https://filedownload.link/file.txt" "File.txt"
#                  This downloads the file from the given URL and saves it
#                  as 'File.txt'
#
getFile() {
  ##### Check input
  #
  # If 2 arguments are given, and if they are not empty strings
  if [ $# -eq 2 ] && [ -n "$1" ] && [ -n "$2" ] ; then
    # Variables that point to file's URL and file name
    FileUrl="${1:="https://raw.githubusercontent.com/Uzay-G/archivy/master/requirements.txt"}"
    FileName="${2:="requirements.txt"}"
  else
    printf '%s\n' "Improper arguments given. Expecting file's URL and name of file." 1>&2 \
      && exit 1
  fi

  ##### Download file
  #
  # If wget is present
  if [ "$(command -v wget)" ] ; then
    # Download the file
    wget -qc "${FileUrl}" -O ./"${FileName}" || (printf '%s\n' "Could not download file from \"${FileUrl}\"." 1>&2 ; exit 1)
  # If cURL is present
  elif [ "$(command -v curl)" ] ; then
    curl "${FileUrl}" --output ./"${FileName}" || (printf '%s\n' "Could not download file from \"${FileUrl}\"." 1>&2 ; exit 1)
  else
    printf '%s\n' "Please install either wget or curl. Required for fetching file from ${FileUrl} file." 1>&2
    exit 1
  fi

  ##### Print path to file
  #
  # If file exists and is not empty
  if [ -s "${FileName}" ] ; then
    # Print the full path to the file
    readlink -f "${FileName}"
  else
    printf '%s\n' "Could not find ${FileName} in ${PWD}." 1>&2 \
      && exit 1
  fi
}


# Function used to filter out comments and empty lines from file
#
# Input  :  Requires one arguments which is the full/relative path to file
#
# Output :  Prints out the file contents without any comments(lines beginning
#           with '#') or empty lines
#
filterComments() {
  # If one argument is provided and it is not an empty string
  if [ $# -eq 1 ] && [ -n "$1" ] ; then
    filePath="$1"
    
    # If file exists and is not empty
    if [ -s "${filePath}" ] ; then
      # Filter out any empty lines and comments(lines beginning with '#')
      # and format as markdown(format as '* `[text]`')
      grep -Ev "^#|^$" "${filePath}" | sed -e 's/^/\*\ `/;s/$/`/'
    fi
  else
    printf '%s\n' "Provide full path to file. Incorrect argument received." 1>&2 \
      && exit 1
  fi
}


# Function used to replace placeholder text
# 
# Input  :  Takes three arguments. First one is the path(relative/absolute)
#           to the file whose contents are to be read. The second argument
#           is the placeholder text which is to be replaced. The third one
#           is the text which is supposed to replace the placeholder.
#
# Output :  Prints text after the placeholder text has been replaced. This
#           DOES NOT modify the file given as input to the function. To
#           modify the file, you will need to redirect the output of this
#           function to the file itself.
#
# Usage  :  replacePlaceholder "/path/to/file" '[placeholder-text]' '[replace-with-text]'
#
replacePlaceholder() {
  ##### Check input
  #
  # If 3 arguments are given, and if the first arguments points to a non-empty file that
  # exists, and if the second and third arguments are not empty strings
  if [ $# -eq 3 ] && [ -s "$1" ] && [ -n "$2" ] && [ -n "$3" ] ; then
    FileName="$(readlink -f "$1")"
    placeholderText="$2"
    replaceWithText="$3"
  # If file does not exist or is empty
  elif [ ! -s "$(readlink -f "$1")" ] ; then
    printf '%s\n' "Could not find ${FileName} in ${PWD}, or ${FileName} is empty." 1>&2 \
      && exit 1
  else
    printf '%s\n' "Incorrect argument(s)." 1>&2 \
      && exit 1
  fi

  ##### Check if placeholder exists in file
  #
  # If the placeholder text could not be found in the file
  if [ "$(grep -o "${placeholderText}" "${FileName}")" = "" ] ; then
    printf '%s\n' "${FileName} did not contain \"${placeholderText}\"." 1>&2 \
      && exit 1
  fi

  # Pass the path to the 'requirements.txt' as an argument to the filterComments function
  # The output of this will be the filtered and formatted text which is assigned to a variable
  #replaceWith="$(filterComments "$(checkIfPresent)")"

  # If 'gawk' utility exists
  if [ "$(command -v gawk)" ] ; then
    ##### Print out content after replacing placeholder
    #
    # The below one-liner prints out the contents of the file after replacing the placeholder text
    gawk -v r="${replaceWithText}" "{gsub(/"${placeholderText}"/,r)}1" "${FileName}" \
      || (printf '%s\n' "Could not replace \"${placeholderText}\" in \"${FileName}\"." 1>&2 && exit 1)
  else
    printf '%s\n' "gawk command not found in PATH. Install gawk." 1>&2 \
      && exit 1
  fi
}


# Main function
#
main() {
  # main "https://link/to/file.txt" 'delimiter' '/path/to/file'
  #
  if [ $# -eq 3 ] && [ -n "$1" ] && [ -n "$2" ] && [ -s "$(readlink -f "$3")" ] ; then
    # This gets the full path of the downloaded file
    replaceFrom="$(getFile "$1" "requirements.txt")" \
      && export replaceFrom="${replaceFrom}"

    placeholderText="$2"
    replaceContentIn="$(readlink -f "$3")"

    # This gets the filtered content from the downloaded file
    filteredContent="$(filterComments "${replaceFrom}")"

    # This prints out text after all placeholders have been replaced
    replacePlaceholder "${replaceContentIn}" "${placeholderText}" "${filteredContent}"
  else
    printf '%s\n' "Incorrect arguments given. Expecting three arguments. First is the URL to the file whose contents \
      will replace the placeholder, second is the placeholder text, third is the file in which the placeholder is to be \
      replaced by the content in the file obtained from the first argument." 1>&2 \
      && exit 1
  fi
}


# Function used to cleanup after.
# This function deletes the 'requirements.txt' file
#
cleanup() {
  # Remove file and unset global variable
  rm "${replaceFrom}" \
    && unset -v replaceFrom
}

# Trapping signals
trap cleanup HUP INT QUIT TRAP TERM

# Calling the 'main' function
main "$@"

# End of script
