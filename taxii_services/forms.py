# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import re
from django import forms

class DataCollectionModelForm(forms.ModelForm):
    """Form for DataCollection objects."""
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
