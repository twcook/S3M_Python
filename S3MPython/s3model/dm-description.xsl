<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl"
    xmlns:dct="http://purl.org/dc/terms/"
    xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    exclude-result-prefixes="xs xd"
    version="2.0">
    <xd:doc scope="stylesheet">
        <xd:desc>
            <xd:p><xd:b>Stylesheet: Created on </xd:b> March 24, 2015</xd:p>
            <xd:p><xd:b>Author:</xd:b>Timothy W. Cook</xd:p>
            <xd:p>Display the detailed description of data based on a S3Model Concept Model.</xd:p>
        </xd:desc>
    </xd:doc>
        
    <xsl:template name="main" match="/">
    <html>
        <head>
            <title><xsl:value-of select="//dct:title"/> -- Data Description</title>
        </head>
        <body bgcolor="d4dadd">
            <xsl:variable name="formlink" select="concat(//dct:identifier,'.html')"/>
            <h2 align="center" style="color:green">Data Description</h2>
            <p>This page describes data from XML instances, based on the concept names. It also provides
            Information from the metadata section of the validating Concept Model (CM) 
            as defined by the knowledge modeler. For a visualization of the nesting structure for the data
            please refer to the <b>HTML form</b> that acccompanies the CM distributed from the 
                <a href='http://builder.s3model.com' target='_blank'>CM Builder</a>.</p>
            <p><xsl:call-template name="metadata"/></p>
            <p><xsl:call-template name="PcT"/></p>
        </body>
    </html>
    </xsl:template>
    
    <xd:doc>
        <xd:desc>
            <xd:p>A table for displaying the CM metadata.</xd:p>
        </xd:desc>
    </xd:doc>
    <xsl:template name="metadata">
    <table title="CM Metadata" align="center" cellpadding="10" border="2" style="width:100%;font-size:12">
        <caption style="font-size:18;font-weight:bold">CM Metadata</caption>
        <tr><th>Name</th><th>Content</th></tr>
        <tr><td><b>Title:</b></td> <td><xsl:value-of select="//dct:title"/></td></tr>
        <tr><td><b>Reference Model:</b></td> <td> <xsl:value-of select="//xs:include/@schemaLocation"/></td></tr>
        <tr><td><b>Author:</b></td> <td> <xsl:value-of select="//dct:creator"/></td></tr>
        <tr><td><b>Contributors:</b></td> <td>
            <xsl:for-each select="//dct:contributor">
                <xsl:value-of select="text()"></xsl:value-of><br/>
            </xsl:for-each></td></tr>
      <tr><td><b>Rights Holder:</b></td> <td> <xsl:value-of select="//dct:rightsHolder"/></td></tr>
        <tr><td><b>Date Issued:</b></td> <td> <xsl:value-of select="//dct:issued"/></td></tr>
        <tr><td><b>License:</b></td> <td> <xsl:value-of select="//dct:license/@rdf:value"/></td></tr>
      <tr><td><b>Language:</b></td> <td> <xsl:value-of select="//dct:language/@rdf:value"/></td></tr>
        <tr><td><b>Description:</b></td> <td> <xsl:value-of select="//dct:abstract"/></td></tr>
    </table>        
    </xsl:template>
        
    <xd:doc>
        <xd:desc>
            <xd:p>Show the modeling information about the data for each complexType.</xd:p>
        </xd:desc>
    </xd:doc>
    <xsl:template name="PcT">
        <table title="CM complexTypes" align="center" cellpadding="10" border="2" style="width:100%;font-size:12">
            <caption style="font-size:18;font-weight:bold">Data Element Descriptions</caption>
            <tr><th>Name</th><th>Definition</th><!--<th>Documentation</th>--><th>XML Element Name</th></tr>
            <xsl:for-each select="//xs:complexType">
                
                <!-- if there is a data-name or cluster subject (because they have a fixed attribute)then create a row -->
                <xsl:if test="xs:complexContent/xs:restriction/xs:sequence/xs:element/@fixed">
                <tr>

                        <td>
                            <xsl:call-template name="dataname"/>
                        </td>                   
                    <td><xsl:value-of select="xs:annotation/xs:documentation"/></td>
                    
<!--                    <td><!-\- decode the isDefinedBy URL if it exists -\->
                        <xsl:variable name="url" select="xs:annotation/xs:appinfo/rdf:Description/rdf:isDefinedBy/@rdf:resource"/>
                        <xsl:call-template name="url-decode">
                            <xsl:with-param name="str" select="$url"/>
                        </xsl:call-template>                        

                    </td>
 -->                   
                    <!-- show the element name for this complexType -->
                    <td><xsl:value-of select="concat('el',translate(@name,'ct',''))"/></td>
                </tr>
                </xsl:if>
            </xsl:for-each>
        </table>
        
    </xsl:template>
    
    <!-- this works because data-name and cluster-subject are the first element in the complexType. -->
    <xsl:template name="dataname">
        <xsl:choose>
            <xsl:when test="contains(xs:complexContent/xs:restriction/@base,'ConceptType')">
               Language: <xsl:value-of select="xs:complexContent/xs:restriction/xs:sequence/xs:element/@fixed"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="xs:complexContent/xs:restriction/xs:sequence/xs:element/@fixed"/>
            </xsl:otherwise>
        </xsl:choose>
            
    </xsl:template>
 
    
    <!-- encoder/decoder courtesy https://gist.github.com/nils-werner/721650 -->
    <xsl:variable name="hex" select="'0123456789ABCDEF'"/>
    <xsl:variable name="ascii"> !"#$%&amp;'()*+,-./0123456789:;&lt;=&gt;?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~</xsl:variable>
    <xsl:variable name="safe">!'()*-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz~</xsl:variable>
    <xsl:variable name="latin1">&#160;&#161;&#162;&#163;&#164;&#165;&#166;&#167;&#168;&#169;&#170;&#171;&#172;&#173;&#174;&#175;&#176;&#177;&#178;&#179;&#180;&#181;&#182;&#183;&#184;&#185;&#186;&#187;&#188;&#189;&#190;&#191;&#192;&#193;&#194;&#195;&#196;&#197;&#198;&#199;&#200;&#201;&#202;&#203;&#204;&#205;&#206;&#207;&#208;&#209;&#210;&#211;&#212;&#213;&#214;&#215;&#216;&#217;&#218;&#219;&#220;&#221;&#222;&#223;&#224;&#225;&#226;&#227;&#228;&#229;&#230;&#231;&#232;&#233;&#234;&#235;&#236;&#237;&#238;&#239;&#240;&#241;&#242;&#243;&#244;&#245;&#246;&#247;&#248;&#249;&#250;&#251;&#252;&#253;&#254;&#255;</xsl:variable>
    
    <xsl:template name="url-decode">
        <xsl:param name="str"/>
        
        <xsl:choose>
            <xsl:when test="contains($str,'%')">
                <xsl:value-of select="substring-before($str,'%')"/>
                <xsl:variable name="hexpair" select="translate(substring(substring-after($str,'%'),1,2),'abcdef','ABCDEF')"/>
                <xsl:variable name="decimal" select="(string-length(substring-before($hex,substring($hexpair,1,1))))*16 + string-length(substring-before($hex,substring($hexpair,2,1)))"/>
                <xsl:choose>
                    <xsl:when test="$decimal &lt; 127 and $decimal &gt; 31">
                        <xsl:value-of select="substring($ascii,$decimal - 31,1)"/>
                    </xsl:when>
                    <xsl:when test="$decimal &gt; 159">
                        <xsl:value-of select="substring($latin1,$decimal - 159,1)"/>
                    </xsl:when>
                    <xsl:otherwise>?</xsl:otherwise>
                </xsl:choose>
                <xsl:call-template name="url-decode">
                    <xsl:with-param name="str" select="substring(substring-after($str,'%'),3)"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <!-- TODO: Make these clickable links. -->
                <xsl:value-of select="$str"/><br/>
                
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    
    <xsl:template name="url-encode">
        <xsl:param name="str"/>
        <xsl:if test="$str">
            <xsl:variable name="first-char" select="substring($str,1,1)"/>
            <xsl:choose>
                <xsl:when test="contains($safe,$first-char)">
                    <xsl:value-of select="$first-char"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:variable name="codepoint">
                        <xsl:choose>
                            <xsl:when test="contains($ascii,$first-char)">
                                <xsl:value-of select="string-length(substring-before($ascii,$first-char)) + 32"/>
                            </xsl:when>
                            <xsl:when test="contains($latin1,$first-char)">
                                <xsl:value-of select="string-length(substring-before($latin1,$first-char)) + 160"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:message terminate="no">Warning: string contains a character that is out of range! Substituting "?".</xsl:message>
                                <xsl:text>63</xsl:text>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:variable name="hex-digit1" select="substring($hex,floor($codepoint div 16) + 1,1)"/>
                    <xsl:variable name="hex-digit2" select="substring($hex,$codepoint mod 16 + 1,1)"/>
                    <xsl:value-of select="concat('%',$hex-digit1,$hex-digit2)"/>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:if test="string-length($str) &gt; 1">
                <xsl:call-template name="url-encode">
                    <xsl:with-param name="str" select="substring($str,2)"/>
                </xsl:call-template>
            </xsl:if>
        </xsl:if>
    </xsl:template>
</xsl:stylesheet>