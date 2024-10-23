import pandas as pd
import glob
import logging
import re
from pathlib import Path
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console
from datetime import datetime
import os
import sys
from collections import Counter
import unicodedata

# Set up Rich console for beautiful output
console = Console()

def setup_logging():
    """Configure logging with both file and console handlers."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            RichHandler(rich_tracebacks=True, markup=True),
            logging.FileHandler(f"logs/processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ]
    )
    return logging.getLogger("leads_unifier")

logger = setup_logging()

def is_likely_name(value):
    """
    Analyze if a string is likely to be a name using multiple heuristics.
    """
    if pd.isna(value):
        return False
        
    value_str = str(value).strip()
    if not value_str:
        return False
        
    # Convert to NFKD normalized form and remove diacritics
    normalized = unicodedata.normalize('NFKD', value_str).encode('ASCII', 'ignore').decode('ASCII')
    
    # Basic checks
    word_count = len(value_str.split())
    if word_count > 6 or word_count < 1:  # Most names are 1-6 words
        return False
        
    # Calculate ratios
    total_chars = len(value_str)
    if total_chars < 2:  # Too short to be a name
        return False
        
    # Count different types of characters
    alpha_count = sum(c.isalpha() or c.isspace() for c in value_str)
    digit_count = sum(c.isdigit() for c in value_str)
    special_count = total_chars - alpha_count - digit_count
    
    # Names should be mostly letters
    alpha_ratio = alpha_count / total_chars
    if alpha_ratio < 0.7:  # At least 70% should be letters or spaces
        return False
        
    # Names shouldn't have many digits
    if digit_count > 0:
        return False
        
    # Check capitalization pattern
    words = value_str.split()
    properly_capitalized = all(word[0].isupper() for word in words if word)
    
    # Calculate final score
    score = 0
    score += alpha_ratio * 5  # Up to 5 points for letter ratio
    score += 2 if properly_capitalized else 0  # 2 points for proper capitalization
    score += 1 if 2 <= word_count <= 4 else 0  # Common name length
    score -= special_count * 0.5  # Penalty for special characters
    
    return score > 3.5  # Threshold determined empirically

def analyze_column_names(columns):
    """
    Analyze column names for name patterns across different languages.
    Returns a dictionary of columns and their scores.
    """
    name_patterns = {
        # English variations
        'name': 5, 'full name': 5, 'full_name': 5, 'firstname': 4, 'lastname': 4,
        'first name': 4, 'last name': 4, 'customer name': 4,
        # Portuguese
        'nome': 5, 'nomes': 5, 'nome completo': 5, 'nome_completo': 5,
        # Spanish
        'nombre': 5, 'nombres': 5, 'nombre completo': 5, 'apellido': 4,
        # French
        'nom': 5, 'prénom': 4, 'prenom': 4, 'nom complet': 5,
        # German
        'name': 5, 'vorname': 4, 'nachname': 4, 'vollständiger name': 5,
        # Italian
        'nome': 5, 'cognome': 4, 'nome completo': 5,
        # Generic
        'contact': 3, 'customer': 3, 'client': 3, 'pessoa': 3, 'person': 3,
        'usuario': 3, 'user': 3, 'lead': 3
    }
    
    scored_columns = {}
    for col in columns:
        col_lower = col.lower().strip()
        
        # Check for exact matches
        if col_lower in name_patterns:
            scored_columns[col] = name_patterns[col_lower]
            continue
            
        # Check for partial matches
        score = 0
        for pattern, pattern_score in name_patterns.items():
            if pattern in col_lower:
                score = max(score, pattern_score - 1)  # Slightly lower score for partial matches
                
        if score > 0:
            scored_columns[col] = score
            
    return scored_columns

def find_name_column(df):
    """
    Find the most likely name column using multiple methods.
    """
    # First, analyze column names
    name_scores = analyze_column_names(df.columns)
    
    # Then, analyze content of potential columns
    for col in df.columns:
        if col not in name_scores:
            # Sample the column (up to 100 values) to check content
            sample = df[col].dropna().astype(str).head(100)
            name_like_ratio = sum(sample.apply(is_likely_name)) / len(sample) if len(sample) > 0 else 0
            
            if name_like_ratio > 0.7:  # If more than 70% of values look like names
                name_scores[col] = 3 * name_like_ratio  # Up to 3 points for content
    
    # Get the column with the highest score
    if name_scores:
        best_column = max(name_scores.items(), key=lambda x: x[1])
        logger.info(f"Found name column: {best_column[0]} (score: {best_column[1]:.2f})")
        return best_column[0]
    
    return None

def is_likely_phone(value):
    """
    Check if a value matches common phone number patterns.
    """
    if pd.isna(value):
        return False
    
    value_str = str(value)
    
    # Remove common separators for checking length
    cleaned = re.sub(r'[\s\-\.\(\)\[\]\{\}]', '', value_str)
    
    # Check maximum length (15 digits per international standard)
    digit_count = sum(c.isdigit() for c in cleaned)
    if digit_count > 15 or digit_count < 8:
        return False
    
    # Basic patterns that indicate a phone number
    patterns = [
        r'^\+?[\d\s\-\.\(\)\[\]\{\}]{8,}$',  # General phone format with optional +
        r'\d{3}[\s\-\.]?\d{3}[\s\-\.]?\d{4}',  # US/NANP format
        r'\+\d{1,3}[\s\-\.]?\d+',  # International format
        r'\(\d{3}\)[\s\-\.]?\d{3}[\s\-\.]?\d{4}',  # (123) 456-7890 format
    ]
    
    return any(re.search(pattern, value_str) for pattern in patterns)

def normalize_phone(phone):
    """Enhanced phone number normalization."""
    if pd.isna(phone):
        return None
        
    phone_str = str(phone)
    
    # Keep original string for length checking
    digits = ''.join(c for c in phone_str if c.isdigit())
    
    # Check if number has acceptable length
    if len(digits) < 8 or len(digits) > 15:
        return None
    
    # Preserve '+' prefix if it exists
    if phone_str.startswith('+'):
        return f"+{digits}"
    return digits

def normalize_email(email):
    """Normalize email addresses by converting to lowercase and stripping whitespace."""
    if pd.isna(email):
        return None
    email_str = str(email).lower().strip()
    return email_str if '@' in email_str else None

def find_column(df, field_type):
    """
    Find a column that likely contains the specified field type.
    Returns the most likely column name or None if not found.
    """
    column_patterns = {
        'name': ['name', 'full name', 'contact', 'customer', 'lead', 'person', 'cliente', 'nombre'],
        'email': ['email', 'e-mail', 'mail', 'correo', 'e_mail', 'e mail', 'correio'],
        'phone': ['phone', 'telephone', 'mobile', 'cell', 'contact', 'tel', 'telefono', 'number', 'celular', 'fone', 'telefone']
    }
    
    # Convert all column names to lowercase for matching
    columns_lower = {col.lower(): col for col in df.columns}
    
    # First try exact matches
    for pattern in column_patterns[field_type]:
        if pattern in columns_lower:
            logger.info(f"Found exact match for {field_type}: {columns_lower[pattern]}")
            return columns_lower[pattern]
    
    # Then try partial matches
    for col_lower, original_col in columns_lower.items():
        for pattern in column_patterns[field_type]:
            if pattern in col_lower:
                logger.info(f"Found partial match for {field_type}: {original_col}")
                return original_col
    
    # If still not found, try fuzzy matching based on content (for emails and phones)
    if field_type == 'email':
        for col in df.columns:
            # Check if column contains @ symbol in majority of non-null values
            if df[col].dtype == 'object' and df[col].notna().any():
                sample = df[col].dropna().astype(str)
                if sample.str.contains('@').mean() > 0.5:
                    logger.info(f"Found email column by content analysis: {col}")
                    return col
    
    elif field_type == 'phone':
        for col in df.columns:
            # Check if column contains mostly numbers
            if df[col].dtype in ['object', 'int64', 'float64'] and df[col].notna().any():
                sample = df[col].dropna().astype(str)
                if sample.str.contains(r'\d').mean() > 0.7:
                    logger.info(f"Found phone column by content analysis: {col}")
                    return col
    
    logger.warning(f"[yellow]Could not find column for {field_type}[/yellow]")
    return None

def find_phone_columns(df):
    """
    Find all columns that might contain phone numbers based on both
    column names and content analysis.
    """
    phone_patterns = {
        # English
        'phone': 5, 'telephone': 5, 'mobile': 5, 'cell': 5, 'contact': 3,
        # Portuguese
        'telefone': 5, 'celular': 5, 'fone': 5, 'tel': 4,
        # Spanish
        'telefono': 5, 'movil': 5, 'celular': 5,
        # French
        'téléphone': 5, 'portable': 5, 'mobile': 5,
        # German
        'telefon': 5, 'handy': 5, 'mobiltelefon': 5,
        # Italian
        'telefono': 5, 'cellulare': 5, 'mobile': 5,
        # Generic
        'contact': 3, 'number': 3, 'phone number': 4, 'tel': 4
    }
    
    phone_columns = []
    
    # Check each column
    for col in df.columns:
        score = 0
        col_lower = col.lower()
        
        # Score based on column name
        for pattern, pattern_score in phone_patterns.items():
            if pattern == col_lower:
                score += pattern_score
            elif pattern in col_lower:
                score += pattern_score - 1
            
        # Score based on content analysis
        if df[col].dtype in ['object', 'int64', 'float64']:
            sample = df[col].dropna().astype(str)
            if len(sample) > 0:
                # Calculate percentage of values that look like phone numbers
                phone_like_ratio = sum(sample.apply(is_likely_phone)) / len(sample)
                score += phone_like_ratio * 4  # Weight content analysis heavily
                
                # Additional score if values have consistent length
                lengths = sample.str.len()
                if lengths.std() < 2 and 8 <= lengths.mean() <= 15:
                    score += 1
                    
        if score > 0:
            phone_columns.append((col, score))
    
    # Sort by score in descending order
    phone_columns.sort(key=lambda x: x[1], reverse=True)
    if phone_columns:
        logger.info(f"Found potential phone columns: {', '.join(f'{col} (score: {score:.2f})' for col, score in phone_columns)}")
    
    return [col for col, _ in phone_columns]

def merge_phone_numbers(row, phone_cols):
    """
    Merge phone numbers from multiple columns, taking the best available number.
    Returns the first valid phone number found after normalization.
    """
    phones = []
    for col in phone_cols:
        if pd.notna(row[col]):
            normalized = normalize_phone(row[col])
            if normalized:
                phones.append(normalized)
    
    # Return the first valid phone number found
    return phones[0] if phones else None

def process_csvs(input_dir="input/*.csv", output_file="output/combined_contacts.csv"):
    """Process all CSV files and combine contact information."""
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Get list of CSV files
    csv_files = glob.glob(input_dir)
    if not csv_files:
        logger.error("[red]No CSV files found in the input directory![/red]")
        return

    # Initialize empty DataFrame to store all contacts
    all_contacts = pd.DataFrame(columns=['name', 'email', 'phone'])
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        main_task = progress.add_task("[cyan]Processing CSV files...", total=len(csv_files))
        
        for csv_file in csv_files:
            file_name = Path(csv_file).name
            logger.info(f"\n[green]Processing file:[/green] {file_name}")
            
            try:
                # Read CSV with all string columns to prevent type inference
                df = pd.read_csv(csv_file, dtype=str, on_bad_lines='warn', encoding_errors='ignore')
                
                # Find columns for each field type
                name_col = find_name_column(df)  # Using new name detection
                email_col = find_column(df, 'email')
                phone_cols = find_phone_columns(df)
                
                found_columns = {
                    'name': name_col,
                    'email': email_col,
                    'phone_columns': phone_cols
                }
                
                logger.info(f"[blue]Found columns:[/blue] {', '.join(f'{k}: {v}' for k, v in found_columns.items() if v)}")
                
                # Create a new DataFrame with standardized columns
                contacts_df = pd.DataFrame()
                
                # Extract and normalize data
                if name_col:
                    contacts_df['name'] = df[name_col].fillna('').astype(str).apply(lambda x: x.strip() or None)
                else:
                    contacts_df['name'] = None
                
                if email_col:
                    contacts_df['email'] = df[email_col].apply(normalize_email)
                else:
                    contacts_df['email'] = None
                
                # Handle phone numbers from multiple columns
                if phone_cols:
                    contacts_df['phone'] = df.apply(lambda row: merge_phone_numbers(row, phone_cols), axis=1)
                else:
                    contacts_df['phone'] = None
                
                # Remove rows where all fields are None or empty strings
                contacts_df = contacts_df.replace('', None)
                valid_contacts = contacts_df.dropna(how='all')
                
                logger.info(f"[green]Successfully extracted[/green] {len(valid_contacts)} contacts from {file_name}")
                
                # Append to main DataFrame
                all_contacts = pd.concat([all_contacts, valid_contacts], ignore_index=True)
                
            except Exception as e:
                logger.error(f"[red]Error processing {file_name}: {str(e)}[/red]")
            
            progress.advance(main_task)
        
        # Remove duplicates
        initial_count = len(all_contacts)
        
        # Sort by completeness (number of non-null fields)
        all_contacts['completeness'] = all_contacts.notna().sum(axis=1)
        all_contacts = all_contacts.sort_values('completeness', ascending=False)
        
        # Remove duplicates based on email OR phone, keeping the most complete record
        deduped_contacts = all_contacts.drop_duplicates(subset=['email'], keep='first')
        deduped_contacts = deduped_contacts.drop_duplicates(subset=['phone'], keep='first')
        
        # Remove helper column
        deduped_contacts = deduped_contacts.drop('completeness', axis=1)
        
        duplicates_removed = initial_count - len(deduped_contacts)
        
        # Save to CSV
        deduped_contacts.to_csv(output_file, index=False)
        
        # Log final statistics
        logger.info("\n[bold green]Processing Complete![/bold green]")
        logger.info(f"[blue]Total files processed:[/blue] {len(csv_files)}")
        logger.info(f"[blue]Total contacts found:[/blue] {initial_count}")
        logger.info(f"[blue]Duplicates removed:[/blue] {duplicates_removed}")
        logger.info(f"[blue]Final unique contacts:[/blue] {len(deduped_contacts)}")
        logger.info(f"[blue]Output saved to:[/blue] {output_file}")
        
        # Display sample of the data
        if not deduped_contacts.empty:
            logger.info("\n[bold blue]Sample of processed data:[/bold blue]")
            console.print(deduped_contacts.head().to_string())
            
            # Display stats about filled values
            filled_stats = deduped_contacts.notna().sum()
            logger.info("\n[bold blue]Field statistics:[/bold blue]")
            for field, count in filled_stats.items():
                percentage = (count / len(deduped_contacts)) * 100
                logger.info(f"{field}: {count} filled values ({percentage:.1f}%)")

def main():
    """Main entry point with error handling."""
    try:
        console.print("[bold magenta]Starting Leads Unifier[/bold magenta]")
        
        # Check for input directory
        if not os.path.exists('input'):
            logger.error("[red]Input directory not found! Creating 'input' directory...[/red]")
            os.makedirs('input')
            logger.info("Please place your CSV files in the 'input' directory and run the script again.")
            return
            
        # Check if input directory is empty
        if not glob.glob('input/*.csv'):
            logger.error("[red]No CSV files found in the input directory![/red]")
            logger.info("Please place your CSV files in the 'input' directory and run the script again.")
            return
            
        process_csvs()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {str(e)}[/red]")
        logger.exception("Fatal error occurred")
        sys.exit(1)

if __name__ == "__main__":
    main()