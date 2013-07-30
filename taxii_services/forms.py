# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import re
from django import forms

class DataFeedModelForm(forms.ModelForm):
    """Form for DataFeed objects."""
    def clean_name(self):
        data = self.cleaned_data["name"]
        
        if re.search(r"\s", data):
            raise forms.ValidationError("Whitespace characters are not allowed")
        
        return data

class InboxModelForm(forms.ModelForm):
    """Form for Inbox objects."""
    def clean_name(self):
        data = self.cleaned_data["name"]
        
        if re.search(r"\s", data):
            raise forms.ValidationError("Whitespace characters are not allowed")
        
        return data
